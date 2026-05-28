"""
Нагрузочное тестирование Department Portal API.

ГЛАВНЫЙ ВОПРОС: нужно ли выносить документы в S3,
или локального хранилища на сервере достаточно?

Как читать результаты:
  Запросы с меткой [meta] — только JSON из БД, диск не задействован.
  Запросы с меткой [file] — реальная отдача файла с диска.
  Итоговый вывод в конце автоматически сравнивает p95 [meta] vs [file]
  и даёт однозначный вердикт про S3.

Сценарии (weight = доля виртуальных пользователей):
  StudentUser   45% — чтение объявлений, событий, метаданных документов, чатов
  TeacherUser   20% — создание объявлений + загрузка документов на диск
  DocHeavyUser  25% — только скачивание файлов (ключевой сценарий для S3-вопроса)
  AdminUser      7% — управление пользователями
  HealthUser     3% — GET /health без авторизации (baseline)

Запуск с веб-интерфейсом:
    locust -f load_tests/locustfile.py --host http://localhost:8000

Headless (из конфига):
    locust -f load_tests/locustfile.py --config load_tests/locust.conf --headless
"""

import io
import os
import random
import string
import threading
from threading import Lock

import requests
from locust import HttpUser, TaskSet, between, events, task
from locust.exception import StopUser

# ── Мониторинг CPU и памяти сервера ──────────────────────────────────────────


class _ServerMonitor:
    """
    Каждые INTERVAL секунд опрашивает GET /metrics на целевом сервере
    и собирает статистику CPU/RAM за время прогона.
    """

    INTERVAL = 5

    def __init__(self):
        self.cpu_samples: list[float] = []
        self.ram_samples: list[float] = []  # RAM процесса FastAPI, МБ
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._host: str = ""

    def start(self, host: str):
        self._host = host.rstrip("/")
        self._thread.start()

    def stop(self):
        self._stop.set()
        self._thread.join(timeout=self.INTERVAL + 1)

    def _run(self):
        while not self._stop.wait(self.INTERVAL):
            try:
                resp = requests.get(f"{self._host}/metrics", timeout=3)
                if resp.status_code == 200:
                    data = resp.json()
                    self.cpu_samples.append(data["cpu_percent"])
                    self.ram_samples.append(data["ram_used_mb"])
            except Exception:
                pass  # сервер недоступен — пропускаем семпл

    def report(self) -> str:
        if not self.cpu_samples:
            return "  Нет данных — убедитесь что /metrics доступен на сервере\n"

        cpu_avg = sum(self.cpu_samples) / len(self.cpu_samples)
        cpu_max = max(self.cpu_samples)
        ram_avg = sum(self.ram_samples) / len(self.ram_samples)
        ram_max = max(self.ram_samples)

        lines = [
            f"  CPU  avg={cpu_avg:.1f}%   max={cpu_max:.1f}%",
            f"  RAM  avg={ram_avg:.0f} MB  max={ram_max:.0f} MB",
            f"  (семплов собрано: {len(self.cpu_samples)})",
        ]
        if cpu_max > 80:
            lines.append("  [!] CPU пиковая > 80% — сервер упирается в процессор")
        if ram_max > 512:
            lines.append("  [!] RAM пик > 512 MB — стоит следить за потреблением")
        return "\n".join(lines)


_monitor = _ServerMonitor()


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    host = environment.host or "http://localhost:8000"
    _monitor.start(host)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    _monitor.stop()


# ── Учётные данные (можно переопределить через env) ───────────────────────────
STUDENT_EMAIL = os.getenv("STUDENT_EMAIL", "student@test.com")
STUDENT_PASSWORD = os.getenv("STUDENT_PASSWORD", "student123")
TEACHER_EMAIL = os.getenv("TEACHER_EMAIL", "teacher@test.com")
TEACHER_PASSWORD = os.getenv("TEACHER_PASSWORD", "teacher123")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@test.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

PREFIX = os.getenv("PREFIX", "/api/v1")

# Общий пул ID загруженных документов: TeacherUser заполняет, DocHeavyUser читает
_doc_ids: list[int] = []
_doc_ids_lock = Lock()


# ── Утилиты ───────────────────────────────────────────────────────────────────


def _rnd(n: int = 8) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=n))


def _login(client, email: str, password: str) -> str | None:
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


def _fake_file(size_kb: int = 50) -> bytes:
    """Синтетический файл заданного размера для тестов загрузки."""
    return b"%PDF-1.4 load-test\n" + b"x" * (size_kb * 1024)


# ── TaskSets ──────────────────────────────────────────────────────────────────


class StudentTasks(TaskSet):
    token: str | None = None
    chat_id: int | None = None

    def on_start(self):
        self.token = _login(self.client, STUDENT_EMAIL, STUDENT_PASSWORD)
        if not self.token:
            raise StopUser()
        # пробуем открыть чат с пользователем id=2 (учитель из фикстур)
        resp = self.client.post(
            f"{PREFIX}/chats/direct/2",
            headers=_hdrs(self.token),
            name="POST /chats/direct [setup]",
        )
        if resp.status_code in (200, 201):
            self.chat_id = resp.json().get("id")

    @task(5)
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

    @task(4)
    def list_documents_meta(self):
        # Метка [meta]: запрос только метаданных — диск не читается
        self.client.get(
            f"{PREFIX}/documents",
            headers=_hdrs(self.token),
            name="GET /documents [meta]",
        )

    @task(2)
    def list_chats(self):
        self.client.get(
            f"{PREFIX}/chats",
            headers=_hdrs(self.token),
            name="GET /chats",
        )

    @task(2)
    def list_chat_messages(self):
        if not self.chat_id:
            return
        self.client.get(
            f"{PREFIX}/chats/{self.chat_id}/messages",
            headers=_hdrs(self.token),
            name="GET /chats/{id}/messages",
        )

    @task(1)
    def get_me(self):
        self.client.get(
            f"{PREFIX}/auth/me",
            headers=_hdrs(self.token),
            name="GET /auth/me",
        )


class TeacherTasks(TaskSet):
    token: str | None = None

    def on_start(self):
        self.token = _login(self.client, TEACHER_EMAIL, TEACHER_PASSWORD)
        if not self.token:
            raise StopUser()
        # Заливаем несколько документов в общий пул при старте
        for _ in range(3):
            self._upload_doc()

    def _upload_doc(self, size_kb: int = 50):
        content = _fake_file(size_kb)
        filename = f"{_rnd()}.pdf"
        with self.client.post(
            f"{PREFIX}/documents",
            headers=_hdrs(self.token),
            data={
                "title": f"Тест {_rnd()}",
                "category": "load-test",
                "visibility": "student,teacher",
            },
            files={"file": (filename, io.BytesIO(content), "application/pdf")},
            catch_response=True,
            name="POST /documents [upload]",
        ) as resp:
            if resp.status_code in (200, 201):
                doc_id = resp.json().get("id")
                if doc_id:
                    with _doc_ids_lock:
                        _doc_ids.append(doc_id)
            else:
                resp.failure(f"[{resp.status_code}] {resp.text[:200]}")

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
        self.client.post(
            f"{PREFIX}/announcements",
            json={"title": f"Объявление {_rnd()}", "content": "Нагрузочный тест."},
            headers=_hdrs(self.token),
            name="POST /announcements",
        )

    @task(1)
    def upload_document(self):
        self._upload_doc()

    @task(1)
    def upload_large_document(self):
        # Большой файл (500 КБ) — проверяем деградацию при росте размера
        self._upload_doc(size_kb=500)


class DocHeavyTasks(TaskSet):
    """
    Целевой сценарий для S3-вопроса.
    25% пользователей только скачивают файлы — максимальная нагрузка на ФС.
    Сравните p95 [file] с p95 [meta] из StudentTasks.
    """

    token: str | None = None

    def on_start(self):
        self.token = _login(self.client, STUDENT_EMAIL, STUDENT_PASSWORD)
        if not self.token:
            raise StopUser()

    @task(8)
    def download_document(self):
        # Метка [file]: реальное чтение файла с диска
        with _doc_ids_lock:
            if not _doc_ids:
                return
            doc_id = random.choice(_doc_ids)

        with self.client.get(
            f"{PREFIX}/documents/{doc_id}/download",
            headers=_hdrs(self.token),
            catch_response=True,
            stream=True,
            name="GET /documents/{id}/download [file]",
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            elif resp.status_code == 404:
                resp.success()  # файл удалён — не считаем ошибкой теста
            else:
                resp.failure(f"[{resp.status_code}] {resp.text[:100]}")

    @task(2)
    def get_document_meta(self):
        # Метка [meta]: тот же документ, но только метаданные из БД
        with _doc_ids_lock:
            if not _doc_ids:
                return
            doc_id = random.choice(_doc_ids)

        self.client.get(
            f"{PREFIX}/documents/{doc_id}",
            headers=_hdrs(self.token),
            name="GET /documents/{id} [meta]",
        )


class AdminTasks(TaskSet):
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

    @task(2)
    def list_announcements(self):
        self.client.get(
            f"{PREFIX}/announcements",
            headers=_hdrs(self.token),
            name="GET /announcements",
        )

    @task(1)
    def list_chats(self):
        self.client.get(
            f"{PREFIX}/chats",
            headers=_hdrs(self.token),
            name="GET /chats",
        )


# ── User-классы ───────────────────────────────────────────────────────────────


class HealthUser(HttpUser):
    weight = 2
    wait_time = between(5, 10)

    @task
    def health(self):
        self.client.get("/health", name="GET /health")


class StudentUser(HttpUser):
    weight = 70
    wait_time = between(8, 25)
    tasks = [StudentTasks]


class TeacherUser(HttpUser):
    weight = 15
    wait_time = between(10, 35)
    tasks = [TeacherTasks]


class DocHeavyUser(HttpUser):
    weight = 10
    wait_time = between(5, 15)
    tasks = [DocHeavyTasks]


class AdminUser(HttpUser):
    weight = 3
    wait_time = between(20, 60)
    tasks = [AdminTasks]


# ── Хук завершения: вердикт по S3 ────────────────────────────────────────────


@events.quitting.add_listener
def on_quit(environment, **kwargs):
    stats = environment.stats
    total = stats.total

    print("\n" + "=" * 65)
    print("ИТОГИ НАГРУЗОЧНОГО ТЕСТИРОВАНИЯ")
    print("=" * 65)
    print(f"  Запросов всего : {total.num_requests}")
    fail_rate = total.num_failures / max(total.num_requests, 1)
    print(f"  Ошибок         : {total.num_failures}  ({fail_rate:.1%})")
    print(f"  RPS (avg)      : {total.current_rps:.1f}")
    print(f"  Latency p50    : {total.get_response_time_percentile(0.50):.0f} ms")
    print(f"  Latency p95    : {total.get_response_time_percentile(0.95):.0f} ms")
    print(f"  Latency p99    : {total.get_response_time_percentile(0.99):.0f} ms")

    # ── Анализ S3 vs локальный диск ───────────────────────────────────────────
    print("\n" + "-" * 65)
    print("НУЖЕН ЛИ S3 ДЛЯ ДОКУМЕНТОВ?")
    print("-" * 65)

    meta_p95_values = [
        e.get_response_time_percentile(0.95)
        for name, e in stats.entries.items()
        if "[meta]" in name and e.num_requests > 0
    ]
    file_p95_values = [
        e.get_response_time_percentile(0.95)
        for name, e in stats.entries.items()
        if "[file]" in name and e.num_requests > 0
    ]

    print("\n" + "-" * 65)
    print("МОНИТОРИНГ CPU И ПАМЯТИ (процесс Locust / тот же хост)")
    print("-" * 65)
    print(_monitor.report())

    if meta_p95_values and file_p95_values:
        p95_meta = max(meta_p95_values)
        p95_file = max(file_p95_values)
        ratio = p95_file / max(p95_meta, 1)

        print(f"  p95 [meta, только БД] : {p95_meta:.0f} ms")
        print(f"  p95 [file, с диска]   : {p95_file:.0f} ms")
        print(f"  Соотношение file/meta : ×{ratio:.1f}")
        print()

        if p95_file > 2000:
            verdict = "НУЖЕН S3 — файлы тормозят (p95 > 2 сек)"
        elif ratio > 3.0:
            verdict = "РЕКОМЕНДОВАН S3 — файлы в 3× медленнее БД"
        elif ratio > 1.5:
            verdict = "S3 ЖЕЛАТЕЛЕН — разница заметна, пока терпимо"
        else:
            verdict = "S3 НЕ НУЖЕН — локальное хранилище справляется"

        print(f"  ВЫВОД: {verdict}")
    else:
        print("  Нет данных для сравнения.")
        print("  Нужны TeacherUser (загрузка) + DocHeavyUser (скачивание).")

    print("=" * 65)

    if fail_rate > 0.01 or total.get_response_time_percentile(0.95) > 2000:
        environment.process_exit_code = 1
