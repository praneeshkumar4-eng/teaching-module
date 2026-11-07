"""
Local file storage engine for LessonForge.
Provides atomic writes (temp file then rename) under data/lessons/<lesson_id>/,
preserving previous versions (v1, v2, v3...), and guaranteeing teacher edits
are never overwritten by failed operations.
"""
import json
import logging
import os
import re
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from config import config
from core.models import (
    LessonMetadata,
    LessonPackage,
    LessonVersion,
    QCFactualReport,
    QCPedagogicalReport,
    ResearchDossier,
    StructuredLessonPlan,
)

logger = logging.getLogger(__name__)


def slugify(text: str) -> str:
    """Generates a clean URL/file-safe slug from a title."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:40] or "lesson"


def get_lesson_dir(lesson_id: str) -> Path:
    """Returns directory path for a lesson ID."""
    return config.data_dir / lesson_id


def atomic_write_text(target_path: Path, content: str):
    """Atomically writes text to disk using a temporary file and atomic replace."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = target_path.parent
    with tempfile.NamedTemporaryFile("w", dir=temp_dir, delete=False, encoding="utf-8") as tf:
        tf.write(content)
        temp_name = tf.name

    os.replace(temp_name, target_path)


def atomic_write_json(target_path: Path, data: dict):
    """Atomically writes JSON to disk using a temporary file and atomic replace."""
    content = json.dumps(data, indent=2, ensure_ascii=False)
    atomic_write_text(target_path, content)


def save_new_lesson(package: LessonPackage) -> str:
    """
    Saves a newly created LessonPackage to disk atomically.
    Creates data/lessons/<lesson_id>/ and saves all JSON and MD files.
    """
    lesson_id = package.metadata.id
    target_dir = get_lesson_dir(lesson_id)
    target_dir.mkdir(parents=True, exist_ok=True)
    versions_dir = target_dir / "versions"
    versions_dir.mkdir(parents=True, exist_ok=True)

    # 1. Save metadata.json
    atomic_write_json(target_dir / "metadata.json", package.metadata.model_dump())

    # 2. Save active lesson.md
    atomic_write_text(target_dir / "lesson.md", package.markdown_content)

    # 3. Save research.json
    atomic_write_json(target_dir / "research.json", package.research_dossier.model_dump())

    # 4. Save QC reports if present
    if package.qc_factual:
        atomic_write_json(target_dir / "qc_factual.json", package.qc_factual.model_dump())

    if package.qc_pedagogical:
        atomic_write_json(target_dir / "qc_pedagogical.json", package.qc_pedagogical.model_dump())

    # 5. Save v1 snapshot in versions/
    atomic_write_text(versions_dir / "v1.md", package.markdown_content)

    history = [
        {
            "version_number": 1,
            "saved_at": datetime.now().isoformat(),
            "note": "Initial generation"
        }
    ]
    atomic_write_json(versions_dir / "history.json", history)

    logger.info(f"Successfully saved new lesson atomically to {target_dir}")
    return lesson_id


def save_lesson_version(lesson_id: str, new_content: str, note: str = "Manual edit") -> int:
    """
    Atomically saves an updated version of the lesson, preserving historical snapshots.
    """
    target_dir = get_lesson_dir(lesson_id)
    if not target_dir.exists():
        raise FileNotFoundError(f"Lesson directory {lesson_id} does not exist.")

    versions_dir = target_dir / "versions"
    versions_dir.mkdir(parents=True, exist_ok=True)

    # Load history
    history_file = versions_dir / "history.json"
    history = []
    if history_file.exists():
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []

    next_version = len(history) + 1

    # Atomic write for new version snapshot
    atomic_write_text(versions_dir / f"v{next_version}.md", new_content)

    # Atomic write for active lesson.md
    atomic_write_text(target_dir / "lesson.md", new_content)

    # Update history log atomically
    history.append({
        "version_number": next_version,
        "saved_at": datetime.now().isoformat(),
        "note": note
    })
    atomic_write_json(history_file, history)

    # Update metadata atomically
    meta_file = target_dir / "metadata.json"
    if meta_file.exists():
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                meta_dict = json.load(f)
            meta_dict["current_version"] = next_version
            meta_dict["total_versions"] = next_version
            meta_dict["updated_at"] = datetime.now().isoformat()
            atomic_write_json(meta_file, meta_dict)
        except Exception as e:
            logger.error(f"Failed to update metadata version: {e}")

    logger.info(f"Saved version v{next_version} for lesson {lesson_id}")
    return next_version


def update_qc_reports(
    lesson_id: str,
    qc_factual: Optional[QCFactualReport] = None,
    qc_pedagogical: Optional[QCPedagogicalReport] = None,
):
    """Atomically updates the saved QC report files for an existing lesson."""
    target_dir = get_lesson_dir(lesson_id)
    if not target_dir.exists():
        return

    if qc_factual:
        atomic_write_json(target_dir / "qc_factual.json", qc_factual.model_dump())

    if qc_pedagogical:
        atomic_write_json(target_dir / "qc_pedagogical.json", qc_pedagogical.model_dump())


def mark_qc_stale(lesson_id: str):
    """Marks existing QC reports as stale following a revision."""
    target_dir = get_lesson_dir(lesson_id)
    if not target_dir.exists():
        return

    for qc_file, model_cls in [("qc_factual.json", QCFactualReport), ("qc_pedagogical.json", QCPedagogicalReport)]:
        path = target_dir / qc_file
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                data["is_stale"] = True
                atomic_write_json(path, data)
            except Exception as e:
                logger.error(f"Failed to mark {qc_file} as stale: {e}")


def load_lesson(lesson_id: str) -> Optional[LessonPackage]:
    """Loads a full LessonPackage from disk."""
    target_dir = get_lesson_dir(lesson_id)
    if not target_dir.exists():
        return None

    try:
        # Load metadata
        meta_file = target_dir / "metadata.json"
        if not meta_file.exists():
            return None
        with open(meta_file, "r", encoding="utf-8") as f:
            metadata = LessonMetadata(**json.load(f))

        # Load active content
        content_file = target_dir / "lesson.md"
        markdown_content = ""
        if content_file.exists():
            with open(content_file, "r", encoding="utf-8") as f:
                markdown_content = f.read()

        # Load research dossier
        research_file = target_dir / "research.json"
        dossier = ResearchDossier(query=metadata.title)
        if research_file.exists():
            with open(research_file, "r", encoding="utf-8") as f:
                dossier = ResearchDossier(**json.load(f))

        # Load QC reports
        qc_factual = None
        qc_fact_file = target_dir / "qc_factual.json"
        if qc_fact_file.exists():
            with open(qc_fact_file, "r", encoding="utf-8") as f:
                qc_factual = QCFactualReport(**json.load(f))

        qc_pedagogical = None
        qc_ped_file = target_dir / "qc_pedagogical.json"
        if qc_ped_file.exists():
            with open(qc_ped_file, "r", encoding="utf-8") as f:
                qc_pedagogical = QCPedagogicalReport(**json.load(f))

        # Load version history
        versions = []
        history_file = target_dir / "versions" / "history.json"
        if history_file.exists():
            with open(history_file, "r", encoding="utf-8") as f:
                history_list = json.load(f)
                for h in history_list:
                    v_num = h["version_number"]
                    v_file = target_dir / "versions" / f"v{v_num}.md"
                    v_content = ""
                    if v_file.exists():
                        with open(v_file, "r", encoding="utf-8") as vf:
                            v_content = vf.read()
                    versions.append(
                        LessonVersion(
                            version_number=v_num,
                            saved_at=h.get("saved_at", ""),
                            note=h.get("note", ""),
                            content=v_content,
                        )
                    )

        return LessonPackage(
            metadata=metadata,
            markdown_content=markdown_content,
            research_dossier=dossier,
            qc_factual=qc_factual,
            qc_pedagogical=qc_pedagogical,
            versions=versions,
        )
    except Exception as e:
        logger.error(f"Failed to load lesson {lesson_id}: {e}")
        return None


def list_all_lessons() -> List[LessonMetadata]:
    """Scans data/lessons/ and returns metadata for all lessons sorted by recency."""
    results = []
    if not config.data_dir.exists():
        return results

    for item in config.data_dir.iterdir():
        if item.is_dir():
            meta_file = item / "metadata.json"
            if meta_file.exists():
                try:
                    with open(meta_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        results.append(LessonMetadata(**data))
                except Exception as e:
                    logger.warning(f"Could not read metadata for {item.name}: {e}")

    results.sort(key=lambda m: m.updated_at, reverse=True)
    return results


def delete_lesson(lesson_id: str) -> bool:
    """Deletes a lesson folder from disk."""
    target_dir = get_lesson_dir(lesson_id)
    if target_dir.exists():
        shutil.rmtree(target_dir)
        logger.info(f"Deleted lesson directory {lesson_id}")
        return True
    return False


def revert_to_version(lesson_id: str, version_number: int) -> bool:
    """Reverts the active lesson content to a historical snapshot."""
    target_dir = get_lesson_dir(lesson_id)
    v_file = target_dir / "versions" / f"v{version_number}.md"
    if not v_file.exists():
        return False

    with open(v_file, "r", encoding="utf-8") as f:
        restored_content = f.read()

    save_lesson_version(lesson_id, restored_content, note=f"Reverted to snapshot v{version_number}")
    return True
