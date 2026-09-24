"""A design document (or other reference file) uploaded against a
specific asset. `stored_filename` is the randomized on-disk name under
`settings.upload_dir` - see infrastructure/storage/local_file_storage.py
- never the user-supplied `original_filename`, which is kept purely for
display and for the filename handed back on download."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class AssetAttachment:
    asset_id: int
    original_filename: str
    stored_filename: str
    uploaded_at: datetime
    attachment_id: Optional[int] = None
    content_type: Optional[str] = None
    file_size: Optional[int] = None
    uploaded_by: Optional[str] = None
