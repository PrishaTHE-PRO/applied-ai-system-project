from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str                        # "low", "medium", "high"
    frequency: Optional[str] = None      # "daily", "weekly", or None
    completed: bool = False
    scheduled_time: Optional[str] = None # "08:00" format

    def mark_complete(self):
        pass

    def reschedule(self, new_time: str):
        pass

    def next_occurrence(self) -> Optional["Task"]:
        pass


@dataclass
class Pet:
    name: str
    species: str
    tasks: list = field(default_factory=list)

    def add_task(self, task: Task):
        pass

    def remove_task(self, task_title: str):
        pass

    def get_tasks(self) -> list:
        pass

    def get_pending_tasks(self) -> list:
        pass


class Owner:
    def __init__(self, name: str, preferences: dict = None):
        self.name = name
        self.pets: list[Pet] = []
        self.preferences: dict = preferences or {}

    def add_pet(self, pet: Pet):
        pass

    def remove_pet(self, pet_name: str):
        pass

    def get_all_tasks(self) -> list:
        pass

    def get_pending_tasks(self) -> list:
        pass


class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner
        self.schedule: list[Task] = []

    def generate_daily_schedule(self) -> list:
        pass

    def sort_by_time(self, tasks: list) -> list:
        pass

    def filter_tasks(self, tasks: list, status: str = None, pet_name: str = None) -> list:
        pass

    def detect_conflicts(self, tasks: list) -> list:
        pass

    def mark_task_complete(self, task: Task):
        pass
