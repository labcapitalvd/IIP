"""Poblado de sections"""

import os

import requests
from shared_db import SessionSync
from shared_utils.logger import get_logger

from models import Form, Section, SectionType


logger = get_logger("seed/sections")


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


def flatten_sections(node, parent_id=None, index_id=None):
    flat = []
    for node_id, content in node.items():
        section = {
            "id": node_id,
            "index_id": content.get("index_id"),
            "parent_id": parent_id if parent_id != "None" else None,
            "section_type_id": content.get("section_type_id"),
            "title": content.get("title"),
            "description": content.get("description"),
            "display_order": content.get("display_order"),
        }
        flat.append(section)

        # Recurse on children
        if "children" in content and content["children"]:
            flat.extend(flatten_sections(content["children"], parent_id=node_id))

    return flat


def upgrade() -> None:
    with SessionSync() as session:
        indexes = session.query(Form).all()
        if not indexes:
            raise RuntimeError("Indexes not found in DB")
        index_lookup = {f"uuid_{i.anno}": i.id for i in indexes}

        sec_types = session.query(SectionType).all()
        if not sec_types:
            raise RuntimeError("Section types not found in DB")
        sec_types_lookup = {f"{i.label}": i.id for i in sec_types}

        full_hier = []
        years = [
            "2021",
            "2023",
            "2025",
        ]

        for i in years:
            local_hier = flatten_sections(hierarchy[f"uuid_{i}"]["children"])
            full_hier.extend(local_hier)

        for section in full_hier:
            idx = section["index_id"]
            if idx not in index_lookup:
                raise RuntimeError(f"Unknown index_id: {idx}")
            section["index_id"] = index_lookup[idx]

            stype = section["section_type_id"]
            if stype not in sec_types_lookup:
                raise RuntimeError(f"Unknown section_type_id: {stype}")
            section["section_type_id"] = sec_types_lookup[stype]

        for section in full_hier:
            exists = session.query(Section).filter_by(id=section["id"]).first()
            if exists:
                logger.info(f"{type} already exists in Section")
                continue  # Skip this one
            session.add(
                Section(
                    id=section["id"],
                    form_id=section["index_id"],
                    parent_id=section["parent_id"],
                    section_type_id=section["section_type_id"],
                    title=section["title"],
                    description=section["description"],
                    display_order=section["display_order"],
                )
            )
            logger.info(f"{type} added to table Section")
        session.commit()
