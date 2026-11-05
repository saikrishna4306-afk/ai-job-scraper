"""Optional cloud helpers.

Core persistence uses SQLAlchemy, so DATABASE_URL can point to PostgreSQL/Supabase.
This small REST client provides private document upload when Supabase Storage is
configured without making cloud credentials mandatory for local development.
"""

from __future__ import annotations

from pathlib import Path


class SupabaseStorage:
    def __init__(self, url: str, key: str, bucket: str):
        self.url, self.key, self.bucket = url.rstrip("/"), key, bucket

    @property
    def configured(self) -> bool:
        return bool(self.url and self.key and self.bucket)

    def upload_private(self, local_path: str | Path, remote_path: str) -> str:
        if not self.configured:
            raise RuntimeError("SUPABASE_URL, SUPABASE_KEY and SUPABASE_STORAGE_BUCKET are required")
        import requests
        path = Path(local_path)
        response = requests.post(f"{self.url}/storage/v1/object/{self.bucket}/{remote_path.lstrip('/')}", headers={"Authorization": f"Bearer {self.key}", "apikey": self.key, "Content-Type": "application/octet-stream", "x-upsert": "true"}, data=path.read_bytes(), timeout=30)
        response.raise_for_status()
        return remote_path
