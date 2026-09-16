"""数据层：Task 数据模型与 JSON 持久化"""
import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional


@dataclass
class Task:
    id: int
    title: str
    priority: str = "normal"  # low / normal / high
    done: bool = False
    created_at: str = ""
    completed_at: Optional[str] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat(timespec="seconds")


class TaskStore:
    """JSON 文件持久化"""

    def __init__(self, path: str = "tasks.json"):
        self.path = path
        self.tasks: List[Task] = []
        self._next_id = 1
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.tasks = [Task(**t) for t in data.get("tasks", [])]
            self._next_id = data.get("next_id", 1)
        else:
            self.tasks = []
            self._next_id = 1

    def _save(self):
        data = {
            "next_id": self._next_id,
            "tasks": [asdict(t) for t in self.tasks],
        }
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add(self, title: str, priority: str = "normal") -> Task:
        if priority not in ("low", "normal", "high"):
            raise ValueError(f"priority must be low/normal/high, got {priority}")
        task = Task(id=self._next_id, title=title, priority=priority)
        self.tasks.append(task)
        self._next_id += 1
        self._save()
        return task

    def complete(self, task_id: int) -> Optional[Task]:
        for t in self.tasks:
            if t.id == task_id:
                t.done = True
                t.completed_at = datetime.now().isoformat(timespec="seconds")
                self._save()
                return t
        return None

    def delete(self, task_id: int) -> bool:
        for i, t in enumerate(self.tasks):
            if t.id == task_id:
                self.tasks.pop(i)
                self._save()
                return True
        return False

    def list(self, only_pending: bool = False) -> List[Task]:
        if only_pending:
            return [t for t in self.tasks if not t.done]
        return self.tasks

    def get(self, task_id: int) -> Optional[Task]:
        for t in self.tasks:
            if t.id == task_id:
                return t
        return None
