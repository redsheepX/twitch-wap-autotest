from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4


@dataclass(frozen=True)
class EvidenceBatch:
    """Owns the single artifact directory shared by one pytest invocation."""

    root: Path
    run_id: str

    @classmethod
    def create(cls, root: Path) -> "EvidenceBatch":
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        return cls(root=root, run_id=f"{timestamp}-{uuid4().hex[:8]}")

    def device_directory(self, device_identifier: str) -> Path:
        path = self.root / self.run_id / device_identifier
        path.mkdir(parents=True, exist_ok=True)
        return path
