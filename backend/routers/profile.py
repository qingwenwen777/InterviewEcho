import json
from datetime import datetime
from io import BytesIO

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from sqlalchemy.orm import Session

from core.llm_service import parse_resume_profile
from db import models, schemas
from db.database import get_db
from services.repo_analyzer import analyze_repo

router = APIRouter()

MAX_RESUME_TEXT_LENGTH = 60000
MAX_RESUME_PDF_BYTES = 10 * 1024 * 1024
MAX_USER_PROJECTS = 8


def get_current_user_id(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization Header")
    try:
        token = authorization.split(" ")[1] if " " in authorization else authorization
        return int(token.replace("fake-token-", ""))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Authorization Token")


def _safe_json_loads(value, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def _json_dumps(value) -> str:
    return json.dumps(value or [], ensure_ascii=False)


def _normalize_url(value: str) -> str:
    return (value or "").strip().rstrip("/")


def _get_or_create_profile(db: Session, user_id: int) -> models.UserProfile:
    profile = db.query(models.UserProfile).filter(models.UserProfile.user_id == user_id).first()
    if profile:
        return profile
    profile = models.UserProfile(user_id=user_id)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def _profile_payload(profile: models.UserProfile | None) -> dict:
    if not profile:
        return schemas.UserProfileData().model_dump()
    return {
        "id": profile.id,
        "display_name": profile.display_name or "",
        "headline": profile.headline or "",
        "target_role": profile.target_role or "",
        "resume_filename": profile.resume_filename or "",
        "resume_text": profile.resume_text or "",
        "resume_summary": profile.resume_summary or "",
        "skills": _safe_json_loads(profile.skills, []),
        "education": _safe_json_loads(profile.education, []),
        "experience": _safe_json_loads(profile.experience, []),
        "projects": _safe_json_loads(profile.projects, []),
        "updated_at": profile.updated_at,
    }


def _project_payload(project: models.UserProject) -> dict:
    summary = _safe_json_loads(project.summary_json, {})
    return {
        "id": project.id,
        "url": project.url,
        "full_name": project.full_name,
        "name": project.name or "",
        "description": project.description or "",
        "main_language": project.main_language or "",
        "stars": project.stars or 0,
        "tech_keywords": _safe_json_loads(project.tech_keywords, []),
        "summary": summary,
        "updated_at": project.updated_at,
    }


async def _apply_resume_text(
    db: Session,
    profile: models.UserProfile,
    resume_text: str,
    *,
    filename: str = "",
    use_ai: bool = True,
) -> models.UserProfile:
    clean_text = (resume_text or "").strip()
    if not clean_text:
        raise HTTPException(status_code=400, detail="简历内容不能为空")
    if len(clean_text) > MAX_RESUME_TEXT_LENGTH:
        clean_text = clean_text[:MAX_RESUME_TEXT_LENGTH]

    parsed = await parse_resume_profile(clean_text) if use_ai else {}
    profile.resume_text = clean_text
    if filename:
        profile.resume_filename = filename[:255]
    profile.resume_summary = (parsed.get("summary") or clean_text[:500]).strip()
    if parsed.get("headline") and not profile.headline:
        profile.headline = parsed.get("headline")
    if parsed.get("target_role") and not profile.target_role:
        profile.target_role = parsed.get("target_role")
    profile.skills = _json_dumps(parsed.get("skills"))
    profile.education = _json_dumps(parsed.get("education"))
    profile.experience = _json_dumps(parsed.get("experience"))
    profile.projects = _json_dumps(parsed.get("projects"))
    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)
    return profile


def _extract_pdf_text(payload: bytes) -> str:
    try:
        from pypdf import PdfReader
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF 解析组件不可用：{type(exc).__name__}")

    try:
        reader = PdfReader(BytesIO(payload))
        chunks = []
        for page in reader.pages[:12]:
            chunks.append(page.extract_text() or "")
        return "\n".join(chunks).strip()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"PDF 解析失败：{type(exc).__name__}")


@router.get("", response_model=schemas.UserProfileResponse)
def get_profile(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    profile = db.query(models.UserProfile).filter(models.UserProfile.user_id == user_id).first()
    projects = (
        db.query(models.UserProject)
        .filter(models.UserProject.user_id == user_id)
        .order_by(models.UserProject.updated_at.desc(), models.UserProject.id.desc())
        .all()
    )
    return {"profile": _profile_payload(profile), "projects": [_project_payload(project) for project in projects]}


@router.put("/resume", response_model=schemas.UserProfileResponse)
async def update_resume(
    data: schemas.ProfileResumeUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    profile = _get_or_create_profile(db, user_id)
    field_limits = {"display_name": 80, "headline": 160, "target_role": 80}
    for field, limit in field_limits.items():
        value = getattr(data, field)
        if value is not None:
            setattr(profile, field, value.strip()[:limit])

    if data.resume_text is not None:
        profile = await _apply_resume_text(db, profile, data.resume_text, use_ai=data.use_ai)
    else:
        profile.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(profile)

    projects = db.query(models.UserProject).filter(models.UserProject.user_id == user_id).all()
    return {"profile": _profile_payload(profile), "projects": [_project_payload(project) for project in projects]}


@router.post("/resume/pdf", response_model=schemas.UserProfileResponse)
async def upload_resume_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    filename = file.filename or "resume.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="请上传 PDF 文件")
    payload = await file.read()
    if len(payload) > MAX_RESUME_PDF_BYTES:
        raise HTTPException(status_code=400, detail="PDF 文件不能超过 10MB")

    text = _extract_pdf_text(payload)
    if len(text) < 20:
        raise HTTPException(status_code=422, detail="没有从 PDF 中识别到可用文本，请尝试复制简历内容手动粘贴。")

    profile = _get_or_create_profile(db, user_id)
    profile = await _apply_resume_text(db, profile, text, filename=filename, use_ai=True)
    projects = db.query(models.UserProject).filter(models.UserProject.user_id == user_id).all()
    return {"profile": _profile_payload(profile), "projects": [_project_payload(project) for project in projects]}


@router.post("/projects", response_model=schemas.UserProjectItem)
async def add_project(
    data: schemas.UserProjectCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    url = _normalize_url(data.url)
    if not url:
        raise HTTPException(status_code=400, detail="GitHub URL 不能为空")

    summary = await analyze_repo(url)
    if summary is None:
        raise HTTPException(status_code=400, detail="无法抓取该 GitHub 仓库，请确认仓库公开且 URL 正确。")

    full_name = summary.get("full_name") or ""
    existing = (
        db.query(models.UserProject)
        .filter(models.UserProject.user_id == user_id)
        .filter((models.UserProject.url == url) | (models.UserProject.full_name == full_name))
        .first()
    )
    project_count = db.query(models.UserProject).filter(models.UserProject.user_id == user_id).count()
    if not existing and project_count >= MAX_USER_PROJECTS:
        raise HTTPException(status_code=400, detail=f"最多保存 {MAX_USER_PROJECTS} 个 GitHub 项目")

    project = existing or models.UserProject(user_id=user_id, url=url, full_name=full_name)
    project.url = summary.get("url") or url
    project.full_name = full_name
    project.name = summary.get("name") or full_name.split("/")[-1]
    project.description = summary.get("description") or ""
    project.main_language = summary.get("main_language") or ""
    project.stars = int(summary.get("stars") or 0)
    project.tech_keywords = _json_dumps(summary.get("tech_keywords"))
    project.summary_json = json.dumps(summary, ensure_ascii=False)
    project.updated_at = datetime.utcnow()
    if not existing:
        db.add(project)
    db.commit()
    db.refresh(project)
    return _project_payload(project)


@router.delete("/projects/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    project = (
        db.query(models.UserProject)
        .filter(models.UserProject.id == project_id, models.UserProject.user_id == user_id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    db.delete(project)
    db.commit()
    return {"ok": True}
