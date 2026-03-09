"""
Парсер расписания сайта edu.sfu-kras.ru.

Сайт СФУ не имеет JSON API — используется HTML-парсинг через BeautifulSoup4.
Параметры запроса — текстовые строки, URL-кодированные через urllib.parse.quote.
"""
from urllib.parse import quote
from typing import Optional
import httpx
from bs4 import BeautifulSoup, Tag
from app.core.cache import schedule_cache

BASE_URL = "https://edu.sfu-kras.ru/timetable"

# Словарь лент → временные интервалы (лента: "НН:НН-НН:НН")
PERIOD_TIMES: dict[int, str] = {
    1: "08:30-10:05",
    2: "10:15-11:50",
    3: "12:00-13:35",
    4: "14:10-15:45",
    5: "15:55-17:30",
    6: "17:40-19:15",
    7: "19:25-21:00",
}


def _parse_cell(cell: Tag, day: str, period: int, time: str, week_type: str) -> Optional[dict]:
    """Парсит одну ячейку таблицы расписания."""
    text = cell.get_text(separator="\n", strip=True)
    if not text:
        return None

    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    if not lines:
        return None

    subject = lines[0]

    # Тип занятия
    lesson_type = "lecture"
    lower = text.lower()
    if any(kw in lower for kw in ["пр.", "практик"]):
        lesson_type = "practice"
    elif any(kw in lower for kw in ["лаб.", "лаборатор"]):
        lesson_type = "lab"

    # Преподаватель — ссылка ?teacher=...
    teacher = ""
    teacher_link = cell.find("a", href=lambda h: h and "teacher=" in str(h))
    if teacher_link:
        teacher = teacher_link.get_text(strip=True)

    # Аудитория
    location = ""
    for line in lines[1:]:
        if any(kw in line for kw in ["ауд", "Корпус", "корпус"]):
            location = line
            break

    # Формат: синхронно / асинхронно
    fmt = "async" if any(kw in lower for kw in ["асинхронно", "async"]) else "sync"

    return {
        "day": day,
        "period": period,
        "time": time,
        "week_type": week_type,
        "subject": subject,
        "type": lesson_type,
        "teacher": teacher,
        "location": location,
        "format": fmt,
    }


def _parse_html(html: str) -> dict:
    """Разбирает HTML-страницу расписания СФУ."""
    soup = BeautifulSoup(html, "lxml")

    # h3 содержит название группы/преподавателя; h1 — логотип сайта
    title_el = soup.find("h3")
    title = title_el.get_text(strip=True) if title_el else ""

    lessons: list[dict] = []
    # Первая таблица на странице — легенда лент, нужна table.timetable
    table = soup.find("table", class_="timetable")
    if not table:
        return {"title": title, "lessons": lessons}

    current_day = ""
    for row in table.find_all("tr"):  # type: ignore[union-attr]
        cells = row.find_all(["td", "th"])

        # Заголовок дня — одна ячейка <th colspan='4'>
        if len(cells) == 1 and cells[0].name == "th":
            current_day = cells[0].get_text(strip=True)
            continue

        # Строка-заголовок колонок (№, Время, ...) — пропускаем
        if not current_day or len(cells) < 3:
            continue

        try:
            period = int(cells[0].get_text(strip=True))
        except ValueError:
            continue

        time = cells[1].get_text(strip=True) or PERIOD_TIMES.get(period, "")

        # Если colspan=2 — одна ячейка для обеих недель
        cell_odd = cells[2]
        colspan = cells[2].get("colspan", "1")
        if str(colspan) == "2":
            # Занятие одинаково на чётной и нечётной неделях
            for week_type in ("odd", "even"):
                entry = _parse_cell(cell_odd, current_day, period, time, week_type)
                if entry:
                    lessons.append(entry)
        else:
            # Раздельные ячейки для нечётной и чётной недель
            for col_idx, week_type in ((2, "odd"), (3, "even")):
                if col_idx >= len(cells):
                    continue
                entry = _parse_cell(cells[col_idx], current_day, period, time, week_type)
                if entry:
                    lessons.append(entry)

    return {"title": title, "lessons": lessons}


async def fetch_group_schedule(sfu_timetable_name: str) -> dict:
    """Получает и парсит расписание группы по её sfu_timetable_name."""
    cache_key = f"group:{sfu_timetable_name}"
    if cache_key in schedule_cache:
        return schedule_cache[cache_key]

    url = f"{BASE_URL}?group={quote(sfu_timetable_name)}"
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()

    result = _parse_html(response.text)
    schedule_cache[cache_key] = result
    return result


async def fetch_teacher_schedule(teacher_name: str) -> dict:
    """Получает и парсит расписание преподавателя по ФИО."""
    cache_key = f"teacher:{teacher_name}"
    if cache_key in schedule_cache:
        return schedule_cache[cache_key]

    url = f"{BASE_URL}?teacher={quote(teacher_name)}"
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()

    result = _parse_html(response.text)
    schedule_cache[cache_key] = result
    return result


def clear_schedule_cache() -> int:
    """Очищает весь кеш расписания. Возвращает число удалённых записей."""
    count = len(schedule_cache)
    schedule_cache.clear()
    return count
