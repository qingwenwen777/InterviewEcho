import asyncio
import json
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from core.config import settings
from db import models, schemas
from db.database import SessionLocal, get_db
from services.judge0_service import (
    LANGUAGE_IDS,
    Judge0Unavailable,
    judge0_service,
    trim_output,
    truncate_text,
)


router = APIRouter()

RUNNING_SUBMISSION_STATUS = "Running"


def get_current_user_id(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization Header")
    try:
        token = authorization.split(" ")[1] if " " in authorization else authorization
        return int(token.replace("fake-token-", ""))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Authorization Token")


def _safe_json(value, default):
    if value in (None, ""):
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def _problem_test_counts(db: Session, problem_id: int):
    all_cases = db.query(models.CodeTestCase).filter(models.CodeTestCase.problem_id == problem_id).all()
    sample_count = sum(1 for item in all_cases if item.is_sample)
    return sample_count, len(all_cases)


def _accepted_problem_ids(db: Session, user_id: int):
    rows = (
        db.query(models.CodeSubmission.problem_id)
        .filter(models.CodeSubmission.user_id == user_id, models.CodeSubmission.status == "Accepted")
        .distinct()
        .all()
    )
    return {row[0] for row in rows}


def _problem_list_item(problem: models.CodeProblem, solved_ids: set, sample_count: int, test_count: int):
    return schemas.CodeProblemListItem(
        id=problem.id,
        title=problem.title,
        slug=problem.slug,
        difficulty=problem.difficulty,
        tags=_safe_json(problem.tags, []),
        source=problem.source or "Hot200",
        solved=problem.id in solved_ids,
        judgable=test_count > 0,
        sample_count=sample_count,
        test_count=test_count,
    )


def _get_problem(db: Session, problem_ref: str):
    query = db.query(models.CodeProblem).filter(models.CodeProblem.is_active == True)
    if str(problem_ref).isdigit():
        problem = query.filter(models.CodeProblem.id == int(problem_ref)).first()
    else:
        problem = query.filter(models.CodeProblem.slug == problem_ref).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    return problem


def _validate_request(payload: schemas.CodeRunRequest):
    language = (payload.language or "").strip().lower()
    if language not in LANGUAGE_IDS:
        raise HTTPException(status_code=400, detail="暂不支持该语言")
    source_code = payload.source_code or ""
    if not source_code.strip():
        raise HTTPException(status_code=400, detail="请先输入完整程序")
    if len(source_code) > settings.CODE_MAX_SOURCE_LENGTH:
        raise HTTPException(status_code=400, detail=f"代码长度不能超过 {settings.CODE_MAX_SOURCE_LENGTH} 个字符")
    return language, source_code


def _status_from_case(result, passed):
    if result.status_id == 3 and passed:
        return "Accepted"
    if result.status_id == 3:
        return "Wrong Answer"
    return result.raw_status


def _case_payload(index, case, result, include_hidden_details):
    actual = trim_output(result.stdout)
    expected = trim_output(case.expected_output)
    passed = result.status_id == 3 and actual == expected
    is_sample = bool(case.is_sample)
    visible = is_sample or include_hidden_details
    message = None
    if not passed and not visible:
        message = "隐藏用例未通过，已隐藏输入与期望输出。"
    elif result.compile_output:
        message = "编译失败，请检查完整程序、类名或语法。"
    elif result.stderr or result.message:
        message = result.stderr or result.message
    elif result.status_id == 3 and not passed:
        message = "输出与期望不一致。"

    return schemas.CodeCaseResult(
        index=index,
        is_sample=is_sample,
        passed=passed,
        status=_status_from_case(result, passed),
        status_description=result.status_description,
        input=case.input if visible else None,
        expected_output=expected if visible else None,
        actual_output=actual if visible or not passed else None,
        stderr=truncate_text(result.stderr),
        compile_output=truncate_text(result.compile_output),
        runtime=result.time,
        memory=result.memory,
        message=message,
    )


async def _run_cases(
    cases: List[models.CodeTestCase],
    language: str,
    source_code: str,
    include_hidden_details: bool,
    precheck_first: bool = True,
):
    results = []
    indexed_cases = list(enumerate(cases, start=1))
    if not indexed_cases:
        return "Wrong Answer", 0, 0, results

    async def run_one(index, case):
        result = await judge0_service.run_code(language, source_code, case.input)
        return _case_payload(index, case, result, include_hidden_details)

    concurrency = max(1, settings.CODE_MAX_CONCURRENT_JUDGE_CASES)
    semaphore = asyncio.Semaphore(concurrency)

    async def run_limited(index, case):
        async with semaphore:
            return await run_one(index, case)

    if precheck_first:
        first_index, first_case = indexed_cases[0]
        first_payload = await run_one(first_index, first_case)
        results.append(first_payload)
        if first_payload.status in {"Compile Error", "Time Limit Exceeded"} or first_payload.status.startswith("Runtime"):
            total_count = len(cases)
            return first_payload.status, 0, total_count, results
        remaining_cases = indexed_cases[1:]
        results.extend(await asyncio.gather(*(run_limited(index, case) for index, case in remaining_cases)))
        results.sort(key=lambda item: item.index)
    else:
        results.extend(await asyncio.gather(*(run_limited(index, case) for index, case in indexed_cases)))
        results.sort(key=lambda item: item.index)

    passed_count = sum(1 for item in results if item.passed)
    total_count = len(cases)
    if passed_count == total_count:
        status = "Accepted"
    else:
        first_failed = next((item for item in results if not item.passed), None)
        status = first_failed.status if first_failed else "Wrong Answer"
    return status, passed_count, total_count, results


def _submission_summary(results: List[schemas.CodeCaseResult], status: str):
    stdout = "\n\n".join([item.actual_output or "" for item in results if item.actual_output]) or None
    stderr = "\n\n".join([item.stderr or "" for item in results if item.stderr]) or None
    compile_output = "\n\n".join([item.compile_output or "" for item in results if item.compile_output]) or None
    result_json = json.dumps([item.model_dump() for item in results], ensure_ascii=False, default=str)
    runtime_values = [item.runtime for item in results if item.runtime is not None]
    memory_values = [item.memory for item in results if item.memory is not None]
    return {
        "status": status,
        "runtime": round(sum(runtime_values), 4) if runtime_values else None,
        "memory": max(memory_values) if memory_values else None,
        "stdout": truncate_text(stdout),
        "stderr": truncate_text(stderr),
        "compile_output": truncate_text(compile_output),
        "result_json": truncate_text(result_json, settings.CODE_OUTPUT_LIMIT * 3),
    }


async def _judge_submission(submission_id: int, case_ids: List[int], language: str, source_code: str):
    db = SessionLocal()
    try:
        cases = (
            db.query(models.CodeTestCase)
            .filter(models.CodeTestCase.id.in_(case_ids))
            .order_by(models.CodeTestCase.sort_order.asc(), models.CodeTestCase.id.asc())
            .all()
        )
        try:
            status, passed_count, total_count, results = await _run_cases(
                cases,
                language,
                source_code,
                False,
                precheck_first=False,
            )
            error_message = None
        except Judge0Unavailable:
            status, passed_count, total_count, results = "Judge Error", 0, len(cases), []
            error_message = "判题服务暂时不可用，请稍后重试"
        except Exception as exc:
            status, passed_count, total_count, results = "Judge Error", 0, len(cases), []
            error_message = truncate_text(str(exc))

        summary = _submission_summary(results, status)
        if error_message and not summary["stderr"]:
            summary["stderr"] = error_message
        submission = db.query(models.CodeSubmission).filter(models.CodeSubmission.id == submission_id).first()
        if not submission:
            return
        submission.status = summary["status"]
        submission.runtime = summary["runtime"]
        submission.memory = summary["memory"]
        submission.passed_count = passed_count
        submission.total_count = total_count
        submission.stdout = summary["stdout"]
        submission.stderr = summary["stderr"]
        submission.compile_output = summary["compile_output"]
        submission.result_json = summary["result_json"]
        db.commit()
    finally:
        db.close()


@router.get("/problems", response_model=schemas.CodeProblemListResponse)
def list_problems(
    difficulty: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    rows = (
        db.query(models.CodeProblem)
        .filter(models.CodeProblem.is_active == True)
        .order_by(models.CodeProblem.order_index.asc(), models.CodeProblem.id.asc())
        .all()
    )
    solved_ids = _accepted_problem_ids(db, user_id)
    all_tags = set()
    items = []
    keyword = (q or "").strip().lower()
    for problem in rows:
        tags = _safe_json(problem.tags, [])
        all_tags.update(tags)
        if difficulty and problem.difficulty != difficulty:
            continue
        if tag and tag not in tags:
            continue
        if keyword and keyword not in problem.title.lower() and keyword not in problem.slug.lower():
            continue
        sample_count, test_count = _problem_test_counts(db, problem.id)
        items.append(_problem_list_item(problem, solved_ids, sample_count, test_count))

    return schemas.CodeProblemListResponse(items=items, tags=sorted(all_tags), total=len(items))


@router.get("/problems/{problem_id}", response_model=schemas.CodeProblemDetail)
def get_problem_detail(problem_id: str, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    problem = _get_problem(db, problem_id)
    solved_ids = _accepted_problem_ids(db, user_id)
    sample_count, test_count = _problem_test_counts(db, problem.id)
    base = _problem_list_item(problem, solved_ids, sample_count, test_count).model_dump()
    return schemas.CodeProblemDetail(
        **base,
        description=problem.description,
        input_format=problem.input_format,
        output_format=problem.output_format,
        samples=_safe_json(problem.samples, []),
        constraints=_safe_json(problem.constraints, []),
        starter_code=_safe_json(problem.starter_code, {}),
    )


@router.post("/problems/{problem_id}/run", response_model=schemas.CodeRunResponse)
async def run_problem(
    problem_id: str,
    payload: schemas.CodeRunRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    del user_id
    problem = _get_problem(db, problem_id)
    language, source_code = _validate_request(payload)
    cases = (
        db.query(models.CodeTestCase)
        .filter(models.CodeTestCase.problem_id == problem.id, models.CodeTestCase.is_sample == True)
        .order_by(models.CodeTestCase.sort_order.asc(), models.CodeTestCase.id.asc())
        .limit(settings.CODE_MAX_TEST_CASES)
        .all()
    )
    if not cases:
        raise HTTPException(status_code=400, detail="这道题暂未开放样例运行")

    try:
        status, passed_count, total_count, results = await _run_cases(cases, language, source_code, True)
    except Judge0Unavailable:
        raise HTTPException(status_code=503, detail="判题服务暂时不可用，请稍后重试")

    return schemas.CodeRunResponse(status=status, passed_count=passed_count, total_count=total_count, results=results)


@router.post("/problems/{problem_id}/submit", response_model=schemas.CodeSubmitResponse)
async def submit_problem(
    problem_id: str,
    payload: schemas.CodeRunRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    problem = _get_problem(db, problem_id)
    if not db.query(models.User.id).filter(models.User.id == user_id).first():
        raise HTTPException(status_code=401, detail="Invalid Authorization Token")
    language, source_code = _validate_request(payload)
    cases = (
        db.query(models.CodeTestCase)
        .filter(models.CodeTestCase.problem_id == problem.id)
        .order_by(models.CodeTestCase.sort_order.asc(), models.CodeTestCase.id.asc())
        .limit(settings.CODE_MAX_TEST_CASES)
        .all()
    )
    if not cases:
        raise HTTPException(status_code=400, detail="这道题还在打磨隐藏测试，暂未开放提交")

    submission = models.CodeSubmission(
        user_id=user_id,
        problem_id=problem.id,
        language=language,
        source_code=source_code,
        status=RUNNING_SUBMISSION_STATUS,
        runtime=None,
        memory=None,
        passed_count=0,
        total_count=len(cases),
        stdout=None,
        stderr=None,
        compile_output=None,
        result_json="[]",
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    background_tasks.add_task(_judge_submission, submission.id, [case.id for case in cases], language, source_code)

    return schemas.CodeSubmitResponse(
        submission_id=submission.id,
        status=RUNNING_SUBMISSION_STATUS,
        passed_count=0,
        total_count=len(cases),
        results=[],
    )


@router.get("/submissions", response_model=List[schemas.CodeSubmissionItem])
def list_submissions(
    problem_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    query = (
        db.query(models.CodeSubmission)
        .filter(models.CodeSubmission.user_id == user_id)
        .order_by(models.CodeSubmission.created_at.desc(), models.CodeSubmission.id.desc())
    )
    if problem_id:
        query = query.filter(models.CodeSubmission.problem_id == problem_id)
    rows = query.limit(80).all()
    return [
        schemas.CodeSubmissionItem(
            id=row.id,
            problem_id=row.problem_id,
            problem_title=row.problem.title if row.problem else None,
            language=row.language,
            status=row.status,
            runtime=row.runtime,
            memory=row.memory,
            passed_count=row.passed_count,
            total_count=row.total_count,
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.get("/submissions/{submission_id}", response_model=schemas.CodeSubmissionDetail)
def get_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    row = (
        db.query(models.CodeSubmission)
        .filter(models.CodeSubmission.id == submission_id, models.CodeSubmission.user_id == user_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Submission not found")
    results = _safe_json(row.result_json, None)
    return schemas.CodeSubmissionDetail(
        id=row.id,
        problem_id=row.problem_id,
        problem_title=row.problem.title if row.problem else None,
        language=row.language,
        status=row.status,
        runtime=row.runtime,
        memory=row.memory,
        passed_count=row.passed_count,
        total_count=row.total_count,
        created_at=row.created_at,
        source_code=row.source_code,
        stdout=row.stdout,
        stderr=row.stderr,
        compile_output=row.compile_output,
        results=results,
    )
