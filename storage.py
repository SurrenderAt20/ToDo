import json
import shutil
from datetime import datetime
from pathlib import Path

from models import Task


STORAGE_DIR = Path.home() / ".todo-widget"
STORAGE_FILE = STORAGE_DIR / "tasks.json"


def _task_to_dict(task: Task) -> dict:
    return {
        "id": task.id,
        "name": task.name,
        "done": task.done,
        "category": task.category,
        "project": task.project,
        "notes": task.notes,
        "created_at": task.created_at.isoformat(),
    }


def _dict_to_task(d: dict) -> Task:
    return Task(
        id=d["id"],
        name=d["name"],
        done=d.get("done", False),
        category=d.get("category"),
        project=d.get("project"),
        notes=d.get("notes"),
        created_at=datetime.fromisoformat(d.get("created_at", datetime.now().isoformat())),
    )


class TaskStorage:
    def __init__(self):
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    def load(self) -> list[Task]:
        if not STORAGE_FILE.exists():
            return []
        try:
            data = json.loads(STORAGE_FILE.read_text(encoding="utf-8"))
            return [_dict_to_task(d) for d in data]
        except (json.JSONDecodeError, KeyError, ValueError):
            backup = STORAGE_FILE.with_suffix(f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            shutil.copy2(STORAGE_FILE, backup)
            return []

    def save(self, tasks: list[Task]) -> None:
        STORAGE_FILE.write_text(
            json.dumps([_task_to_dict(t) for t in tasks], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def add(self, task: Task) -> None:
        tasks = self.load()
        tasks.append(task)
        self.save(tasks)

    def update(self, task_id: str, **kwargs) -> None:
        tasks = self.load()
        for task in tasks:
            if task.id == task_id:
                for key, value in kwargs.items():
                    if hasattr(task, key):
                        setattr(task, key, value)
                break
        self.save(tasks)

    def delete(self, task_id: str) -> None:
        tasks = self.load()
        tasks = [t for t in tasks if t.id != task_id]
        self.save(tasks)
