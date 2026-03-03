"""Poblado de questions desde hierarchy.json"""

import os

import requests
from shared_db import SessionSync
from shared_utils.logger import get_logger

from models import Form, Question


logger = get_logger("SeedQuestions")


ORIGIN_URL = "https://api.github.com/repos/LABCapital-VD/IIP-Cuadernos-Jupyter/contents/Gestión/Estructura IIP/output/hierarchy.json"

GITHUB_TOKEN_FILE = "/run/secrets/github_token_seeds"
if not os.path.exists(GITHUB_TOKEN_FILE):
    raise FileNotFoundError(f"GITHUB_TOKEN_FILE file not found at {GITHUB_TOKEN_FILE}")
with open(GITHUB_TOKEN_FILE, "r") as f:
    GITHUB_TOKEN = f.read().strip()

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3.raw",
}
r = requests.get(ORIGIN_URL, headers=headers)
r.raise_for_status()  # fail if not 200
hierarchy = r.json()


def flatten_questions(node):
    """Recursively extract all questions nested under 'children' and 'questions'."""
    flat = []
    for node_id, content in node.items():
        # If there are questions directly under this section
        if "questions" in content and content["questions"]:
            for q_id, q_data in content["questions"].items():
                flat.append(
                    {
                        "id": q_id,
                        "index_id": q_data.get("index_id"),
                        "section_id": q_data.get("section_id"),
                        "is_loop": q_data.get("is_loop") == "True",
                        "title": q_data.get("title"),
                        "description": q_data.get("description"),
                        "display_order": q_data.get("display_order"),
                        "required": q_data.get("required") == "True",
                        "peso": q_data.get("peso"),
                    }
                )

        # Recurse on children sections if any
        if "children" in content and content["children"]:
            flat.extend(flatten_questions(content["children"]))

    return flat


def upgrade() -> None:
    with SessionSync() as session:
        forms = session.query(Form).all()
        if not forms:
            raise RuntimeError("Forms not found in DB")

        form_lookup = {f"uuid_{f.anno}": f.id for f in forms}

        # Aggregate questions across all years
        all_questions = []
        years = ["2021", "2023", "2025"]

        for year in years:
            year_key = f"uuid_{year}"
            root = hierarchy.get(year_key)
            if not root:
                logger.warning(f"Missing year {year_key} in hierarchy.json")
                continue
            questions = flatten_questions(root["children"])
            for q in questions:
                # Replace form key with actual UUID
                idx = q["index_id"]
                if idx not in form_lookup:
                    raise RuntimeError(f"Unknown index_id: {idx}")
                q["index_id"] = form_lookup[idx]
            all_questions.extend(questions)

        logger.info(f"Found {len(all_questions)} questions total")

        # Insert questions if not already present
        for q in all_questions:
            exists = session.query(Question).filter_by(id=q["id"]).first()
            if exists:
                logger.info(f"{type} already exists in Question")
                continue

            session.add(
                Question(
                    id=q["id"],
                    form_id=q["index_id"],
                    section_id=q["section_id"],
                    title=q["title"],
                    description=q["description"],
                    display_order=q["display_order"],
                    required=q["required"],
                    is_loop=q["is_loop"],
                )
            )
            logger.info(f"{type} added to table Question")

        session.commit()
