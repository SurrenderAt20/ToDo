from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class Task:
    name: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    done: bool = False
    category: str | None = None
    project: str | None = None
    notes: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
