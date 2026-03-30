import pytest
from datetime import date, timedelta
from pawpal_system import Task, Pet, Owner, Scheduler


# ── Task ──────────────────────────────────────────────────────────────────────

def test_task_mark_complete():
    task = Task(title="Walk", duration_minutes=20, priority="high")
    task.mark_complete()
    assert task.completed is True


def test_task_reschedule():
    task = Task(title="Walk", duration_minutes=20, priority="high", scheduled_time="08:00")
    task.reschedule("10:00")
    assert task.scheduled_time == "10:00"


def test_task_next_occurrence_daily():
    """Daily recurrence schedules exactly one day from today."""
    task = Task(title="Walk", duration_minutes=20, priority="high",
                frequency="daily", scheduled_time="08:00")
    next_task = task.next_occurrence()
    expected_date = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    assert next_task is not None
    assert next_task.scheduled_time == f"{expected_date} 08:00"
    assert next_task.completed is False


def test_task_next_occurrence_weekly():
    """Weekly recurrence schedules exactly seven days from today."""
    task = Task(title="Bath", duration_minutes=30, priority="low",
                frequency="weekly", scheduled_time="10:00")
    next_task = task.next_occurrence()
    expected_date = (date.today() + timedelta(weeks=1)).strftime("%Y-%m-%d")
    assert next_task is not None
    assert next_task.scheduled_time == f"{expected_date} 10:00"


def test_task_next_occurrence_no_frequency():
    """Non-recurring tasks return None."""
    task = Task(title="Walk", duration_minutes=20, priority="high")
    assert task.next_occurrence() is None


def test_task_next_occurrence_no_time_uses_default():
    """Recurring task with no scheduled_time defaults to 08:00 for next occurrence."""
    task = Task(title="Meds", duration_minutes=5, priority="high", frequency="daily")
    next_task = task.next_occurrence()
    assert next_task is not None
    assert next_task.scheduled_time.endswith("08:00")


# ── Pet ───────────────────────────────────────────────────────────────────────

def test_pet_add_and_get_tasks():
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task(title="Walk", duration_minutes=20, priority="high"))
    assert len(pet.get_tasks()) == 1


def test_pet_remove_task():
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task(title="Walk", duration_minutes=20, priority="high"))
    pet.remove_task("Walk")
    assert pet.get_tasks() == []


def test_pet_get_pending_tasks():
    pet = Pet(name="Mochi", species="dog")
    done = Task(title="Bath", duration_minutes=30, priority="low")
    done.mark_complete()
    pending = Task(title="Walk", duration_minutes=20, priority="high")
    pet.add_task(done)
    pet.add_task(pending)
    assert pet.get_pending_tasks() == [pending]


def test_pet_with_no_tasks():
    """Edge case: a pet with no tasks returns empty lists without error."""
    pet = Pet(name="Ghost", species="cat")
    assert pet.get_tasks() == []
    assert pet.get_pending_tasks() == []


# ── Owner ─────────────────────────────────────────────────────────────────────

def test_owner_add_and_get_all_tasks():
    owner = Owner(name="Jordan")
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task(title="Walk", duration_minutes=20, priority="high"))
    owner.add_pet(pet)
    assert len(owner.get_all_tasks()) == 1


def test_owner_remove_pet():
    owner = Owner(name="Jordan")
    owner.add_pet(Pet(name="Mochi", species="dog"))
    owner.remove_pet("Mochi")
    assert owner.pets == []


def test_owner_get_pending_tasks_across_pets():
    owner = Owner(name="Jordan")
    dog = Pet(name="Mochi", species="dog")
    cat = Pet(name="Luna", species="cat")
    dog.add_task(Task(title="Walk", duration_minutes=20, priority="high"))
    cat.add_task(Task(title="Feed", duration_minutes=5, priority="high"))
    owner.add_pet(dog)
    owner.add_pet(cat)
    assert len(owner.get_pending_tasks()) == 2


def test_owner_with_no_pets_returns_empty():
    """Edge case: owner with no pets has no tasks."""
    owner = Owner(name="Nobody")
    assert owner.get_all_tasks() == []
    assert owner.get_pending_tasks() == []


# ── Scheduler — sorting ───────────────────────────────────────────────────────

def test_sort_by_time_chronological():
    """Tasks added out of order are returned in HH:MM ascending order."""
    owner = Owner(name="Jordan")
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task(title="Evening Walk", duration_minutes=20, priority="medium", scheduled_time="18:00"))
    pet.add_task(Task(title="Feeding",      duration_minutes=5,  priority="high",   scheduled_time="08:00"))
    pet.add_task(Task(title="Grooming",     duration_minutes=15, priority="low",    scheduled_time="12:00"))
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    sorted_tasks = scheduler.sort_by_time(pet.get_tasks())
    times = [t.scheduled_time for t in sorted_tasks]
    assert times == sorted(times)


def test_sort_by_time_unscheduled_tasks_last():
    """Tasks with no scheduled_time sort after all timed tasks."""
    owner = Owner(name="Jordan")
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task(title="Unscheduled", duration_minutes=10, priority="high"))
    pet.add_task(Task(title="Morning",     duration_minutes=20, priority="high", scheduled_time="07:00"))
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    result = scheduler.sort_by_time(pet.get_tasks())
    assert result[0].title == "Morning"
    assert result[-1].title == "Unscheduled"


def test_scheduler_generate_schedule_order():
    owner = Owner(name="Jordan")
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task(title="Walk", duration_minutes=20, priority="high", scheduled_time="08:00"))
    pet.add_task(Task(title="Bath", duration_minutes=30, priority="low",  scheduled_time="07:00"))
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    schedule = scheduler.generate_daily_schedule()
    times = [t.scheduled_time for t in scheduler.sort_by_time(schedule)]
    assert times == sorted(times)


# ── Scheduler — filtering ─────────────────────────────────────────────────────

def test_scheduler_filter_by_status():
    owner = Owner(name="Jordan")
    pet = Pet(name="Mochi", species="dog")
    done = Task(title="Bath", duration_minutes=30, priority="low",  scheduled_time="07:00")
    done.mark_complete()
    active = Task(title="Walk", duration_minutes=20, priority="high", scheduled_time="08:00")
    pet.add_task(done)
    pet.add_task(active)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    all_tasks = owner.get_all_tasks()
    assert scheduler.filter_tasks(all_tasks, status="pending") == [active]
    assert scheduler.filter_tasks(all_tasks, status="completed") == [done]


def test_scheduler_filter_by_pet_name():
    """filter_tasks(pet_name=) returns only tasks belonging to that pet."""
    owner = Owner(name="Jordan")
    dog = Pet(name="Mochi", species="dog")
    cat = Pet(name="Luna",  species="cat")
    walk = Task(title="Walk", duration_minutes=20, priority="high")
    feed = Task(title="Feed", duration_minutes=5,  priority="high")
    dog.add_task(walk)
    cat.add_task(feed)
    owner.add_pet(dog)
    owner.add_pet(cat)
    scheduler = Scheduler(owner)
    result = scheduler.filter_tasks(owner.get_all_tasks(), pet_name="Mochi")
    assert result == [walk]
    assert feed not in result


# ── Scheduler — conflict detection ────────────────────────────────────────────

def test_scheduler_no_conflicts():
    owner = Owner(name="Jordan")
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task(title="Walk", duration_minutes=20, priority="high",   scheduled_time="08:00"))
    pet.add_task(Task(title="Feed", duration_minutes=10, priority="medium", scheduled_time="09:00"))
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    schedule = scheduler.generate_daily_schedule()
    assert scheduler.detect_conflicts(schedule) == []


def test_scheduler_detects_overlap():
    """Two tasks whose windows overlap produce one warning string."""
    owner = Owner(name="Jordan")
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task(title="Walk", duration_minutes=60, priority="high",   scheduled_time="08:00"))
    pet.add_task(Task(title="Bath", duration_minutes=30, priority="medium", scheduled_time="08:30"))
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    schedule = scheduler.generate_daily_schedule()
    warnings = scheduler.detect_conflicts(schedule)
    assert len(warnings) == 1
    assert "Walk" in warnings[0]
    assert "Bath" in warnings[0]


def test_scheduler_detects_exact_same_start_time():
    """Edge case: two tasks starting at identical times are a conflict."""
    owner = Owner(name="Jordan")
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task(title="Walk", duration_minutes=20, priority="high",   scheduled_time="09:00"))
    pet.add_task(Task(title="Meds", duration_minutes=10, priority="high",   scheduled_time="09:00"))
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    schedule = scheduler.generate_daily_schedule()
    warnings = scheduler.detect_conflicts(schedule)
    assert len(warnings) >= 1


def test_scheduler_conflict_returns_warning_string():
    """detect_conflicts returns strings, not tuples."""
    owner = Owner(name="Jordan")
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task(title="A", duration_minutes=60, priority="high", scheduled_time="08:00"))
    pet.add_task(Task(title="B", duration_minutes=30, priority="high", scheduled_time="08:15"))
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    schedule = scheduler.generate_daily_schedule()
    warnings = scheduler.detect_conflicts(schedule)
    assert all(isinstance(w, str) for w in warnings)


# ── Scheduler — recurring tasks ───────────────────────────────────────────────

def test_scheduler_mark_task_complete_recurring():
    """Completing a daily task adds a new pending occurrence to the pet."""
    owner = Owner(name="Jordan")
    pet = Pet(name="Mochi", species="dog")
    task = Task(title="Walk", duration_minutes=20, priority="high",
                frequency="daily", scheduled_time="08:00")
    pet.add_task(task)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    scheduler.mark_task_complete(task)
    assert task.completed is True
    pending = pet.get_pending_tasks()
    assert len(pending) == 1
    assert pending[0].title == "Walk"


def test_scheduler_mark_complete_non_recurring_no_new_task():
    """Completing a one-off task does not create a new occurrence."""
    owner = Owner(name="Jordan")
    pet = Pet(name="Mochi", species="dog")
    task = Task(title="Vet Visit", duration_minutes=60, priority="high")
    pet.add_task(task)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    scheduler.mark_task_complete(task)
    assert pet.get_pending_tasks() == []


def test_scheduler_empty_owner_generates_empty_schedule():
    """Edge case: owner with no pets or tasks produces an empty schedule."""
    owner = Owner(name="Nobody")
    scheduler = Scheduler(owner)
    assert scheduler.generate_daily_schedule() == []
