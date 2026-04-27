"""
Нагрузочное тестирование Department Portal API.
Цель: 1000 RPS, p95 < 2000 ms, error rate < 1%.

Сценарии (weight = доля пользователей):
  HealthUser   5%  — GET /health (без авторизации)
  StudentUser  70% — объявления + события
  TeacherUser  20% — чтение + создание объявлений/событий
  AdminUser    10% — пользователи + сообщения

Запуск (web UI):
    locust -f load_tests/locustfile.py --host http://localhost:8000

Headless 1000 RPS (~500 виртуальных пользователей):
    locust -f load_tests/locustfile.py \
           --config load_tests/locust.conf \
           --headless

Env-переменные для учётных данных:
    STUDENT_EMAIL, STUDENT_PASSWORD
    TEACHER_EMAIL, TEACHER_PASSWORD
    ADMIN_EMAIL,   ADMIN_PASSWORD
"""

import os
import random
import string

from locust import HttpUser, TaskSet, task, between, events
from locust.exception import StopUser

# ── Учётные данные ────────────────────────────────────────────────────────────
STUDENT_EMAIL    = os.getenv("STUDENT_EMAIL",    "student@test.com")
STUDENT_PASSWORD = os.getenv("STUDENT_PASSWORD", "student123")

TEACHER_EMAIL    = os.getenv("TEACHER_EMAIL",    "teacher@test.com")
TEACHER_PASSWORD = os.getenv("TEACHER_PASSWORD", "teacher123")

ADMIN_EMAIL      = os.getenv("ADMIN_EMAIL",      "admin@test.com")
ADMIN_PASSWORD   = os.getenv("ADMIN_PASSWORD",   "admin123")

PREFIX = "/api/v1"


# ── Утилиты ───────────────────────────────────────────────────────────────────

def _rnd(n: int = 8) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=n))


def _login(client, email: str, password: str) -> str | None:
    """
    Авторизация через OAuth2PasswordRequestForm (form-data, не JSON).
    Возвращает access_token или None при ошибке.
    """
    with client.post(
        f"{PREFIX}/auth/login",
        data={"username": email, "password": password},
        catch_response=True,
        name="POST /auth/login",
    ) as resp:
        if resp.status_code == 200:
            return resp.json().get("access_token")
        resp.failure(f"[{resp.status_code}] {resp.text[:200]}")
        return None


def _hdrs(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── TaskSets ──────────────────────────────────────────────────────────────────

class StudentTasks(TaskSet):
    """Студент: только чтение публичного контента."""

    token: str | None = None

    def on_start(self):
        self.token = _login(self.client, STUDENT_EMAIL, STUDENT_PASSWORD)
        if not self.token:
            raise StopUser()

    @task(5)
    def list_announcements(self):
        self.client.get(
            f"{PREFIX}/announcements",
            headers=_hdrs(self.token),
            name="GET /announcements",
        )

    @task(4)
    def list_events(self):
        self.client.get(
            f"{PREFIX}/events",
            headers=_hdrs(self.token),
            name="GET /events",
        )

    @task(1)
    def list_events_with_dates(self):
        self.client.get(
            f"{PREFIX}/events?from_dt=2025-01-01T00:00:00&to_dt=2026-12-31T23:59:59",
            headers=_hdrs(self.token),
            name="GET /events?date_range",
        )


class TeacherTasks(TaskSet):
    """Учитель: чтение + публикация объявлений и событий."""

    token: str | None = None

    def on_start(self):
        self.token = _login(self.client, TEACHER_EMAIL, TEACHER_PASSWORD)
        if not self.token:
            raise StopUser()

    @task(4)
    def list_announcements(self):
        self.client.get(
            f"{PREFIX}/announcements",
            headers=_hdrs(self.token),
            name="GET /announcements",
        )

    @task(3)
    def list_events(self):
        self.client.get(
            f"{PREFIX}/events",
            headers=_hdrs(self.token),
            name="GET /events",
        )

    @task(2)
    def create_announcement(self):
        with self.client.post(
            f"{PREFIX}/announcements",
            json={"title": f"Load test {_rnd()}", "content": "Тест нагрузки."},
            headers=_hdrs(self.token),
            catch_response=True,
            name="POST /announcements",
        ) as resp:
            if resp.status_code not in (200, 201):
                resp.failure(f"[{resp.status_code}] {resp.text[:200]}")

    @task(1)
    def create_event(self):
        with self.client.post(
            f"{PREFIX}/events",
            json={
                "title": f"Event {_rnd()}",
                "description": "Нагрузочный тест.",
                "starts_at": "2026-09-01T10:00:00",
                "ends_at": "2026-09-01T12:00:00",
            },
            headers=_hdrs(self.token),
            catch_response=True,
            name="POST /events",
        ) as resp:
            if resp.status_code not in (200, 201):
                resp.failure(f"[{resp.status_code}] {resp.text[:200]}")


class AdminTasks(TaskSet):
    """Администратор: управление пользователями, мониторинг."""

    token: str | None = None

    def on_start(self):
        self.token = _login(self.client, ADMIN_EMAIL, ADMIN_PASSWORD)
        if not self.token:
            raise StopUser()

    @task(3)
    def list_users(self):
        self.client.get(
            f"{PREFIX}/users?skip=0&limit=50",
            headers=_hdrs(self.token),
            name="GET /users",
        )

    @task(3)
    def list_events(self):
        self.client.get(
            f"{PREFIX}/events",
            headers=_hdrs(self.token),
            name="GET /events",
        )

    @task(2)
    def list_announcements(self):
        self.client.get(
            f"{PREFIX}/announcements",
            headers=_hdrs(self.token),
            name="GET /announcements",
        )

    @task(2)
    def list_messages(self):
        self.client.get(
            f"{PREFIX}/messages",
            headers=_hdrs(self.token),
            name="GET /messages",
        )


# ── User-классы ───────────────────────────────────────────────────────────────

class HealthUser(HttpUser):
    """Smoke без авторизации — только /health."""

    weight = 5
    wait_time = between(0.05, 0.2)

    @task
    def health(self):
        self.client.get("/health", name="GET /health")


class StudentUser(HttpUser):
    weight = 70
    wait_time = between(0.1, 0.5)
    tasks = [StudentTasks]


class TeacherUser(HttpUser):
    weight = 20
    wait_time = between(0.2, 1.0)
    tasks = [TeacherTasks]


class AdminUser(HttpUser):
    weight = 10
    wait_time = between(0.5, 2.0)
    tasks = [AdminTasks]


# ── Хук завершения: критерии качества ────────────────────────────────────────

@events.quitting.add_listener
def on_quit(environment, **kwargs):
    stats = environment.stats
    total = stats.total

    print("\n" + "=" * 60)
    print("ИТОГИ НАГРУЗОЧНОГО ТЕСТИРОВАНИЯ")
    print("=" * 60)
    print(f"  Запросов всего : {total.num_requests}")
    print(f"  Ошибок         : {total.num_failures}")
    print(f"  RPS (avg)      : {total.current_rps:.1f}")
    print(f"  Latency p50    : {total.get_response_time_percentile(0.50):.0f} ms")
    print(f"  Latency p95    : {total.get_response_time_percentile(0.95):.0f} ms")
    print(f"  Latency p99    : {total.get_response_time_percentile(0.99):.0f} ms")
    print("=" * 60)

    fail_rate = total.num_failures / max(total.num_requests, 1)
    p95 = total.get_response_time_percentile(0.95)

    if fail_rate > 0.01:
        print(f"[FAIL] Ошибок {fail_rate:.1%} > порога 1%")
        environment.process_exit_code = 1
    elif p95 > 2000:
        print(f"[FAIL] p95 latency {p95:.0f} ms > порога 2000 ms")
        environment.process_exit_code = 1
    else:
        print("[OK] Все критерии выполнены")
