import json

from db import models
from db.code_problem_bank import get_hot100_problems


def _dump(value):
    return json.dumps(value, ensure_ascii=False)


def seed_code_problems(db):
    """Insert or refresh Hot100 ACM problem metadata and test cases."""
    for order_index, item in enumerate(get_hot100_problems(), start=1):
        problem = db.query(models.CodeProblem).filter(models.CodeProblem.id == item["id"]).first()
        fields = {
            "title": item["title"],
            "slug": item["slug"],
            "difficulty": item["difficulty"],
            "tags": _dump(item["tags"]),
            "description": item["description"],
            "input_format": item["input_format"],
            "output_format": item["output_format"],
            "samples": _dump(item["samples"]),
            "constraints": _dump(item["constraints"]),
            "starter_code": _dump(item["starter_code"]),
            "source": "Hot100",
            "is_active": True,
            "order_index": order_index,
        }

        if problem is None:
            problem = models.CodeProblem(id=item["id"], **fields)
            db.add(problem)
            db.flush()
        else:
            for key, value in fields.items():
                setattr(problem, key, value)

        db.query(models.CodeTestCase).filter(models.CodeTestCase.problem_id == problem.id).delete()
        for case_index, case in enumerate(item["test_cases"], start=1):
            db.add(
                models.CodeTestCase(
                    problem_id=problem.id,
                    input=case["input"],
                    expected_output=case["expected_output"],
                    is_sample=bool(case.get("is_sample")),
                    explanation=case.get("explanation"),
                    sort_order=case_index,
                )
            )

    db.commit()
