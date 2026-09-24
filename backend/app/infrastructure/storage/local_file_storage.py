"""Local-disk storage for uploaded files - asset design-document
attachments and the platform logo. Everything lives under
`settings.upload_dir`, split into subdirectories per use.

Files are saved under a random UUID-based name, never the user-supplied
original filename: that avoids both path-traversal (a filename like
"../../etc/passwd") and same-name collisions between uploads. The
original filename is kept separately (in the DB, for attachments; not
at all for the logo, which has no meaningful original name) purely for
display and for the filename handed back on download.
"""
from __future__ import annotations

import uuid
from pathlib import Path

from app.infrastructure.config.settings import get_settings

ATTACHMENTS_SUBDIR = "attachments"
BRANDING_SUBDIR = "branding"


def _subdir_path(subdir: str) -> Path:
    path = Path(get_settings().upload_dir) / subdir
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_file(subdir: str, original_filename: str, content: bytes) -> str:
    """Writes `content` under `<upload_dir>/<subdir>/<random-name>` and
    returns the stored filename (unique within `subdir`) to persist."""
    suffix = Path(original_filename).suffix.lower()
    stored_name = f"{uuid.uuid4().hex}{suffix}"
    (_subdir_path(subdir) / stored_name).write_bytes(content)
    return stored_name


def read_file(subdir: str, stored_filename: str) -> bytes:
    return (_subdir_path(subdir) / stored_filename).read_bytes()


def delete_file(subdir: str, stored_filename: str) -> None:
    (_subdir_path(subdir) / stored_filename).unlink(missing_ok=True)


def file_exists(subdir: str, stored_filename: str) -> bool:
    return (_subdir_path(subdir) / stored_filename).is_file()
