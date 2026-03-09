"""
Тесты парсера расписания СФУ.
Httpx-запросы к edu.sfu-kras.ru мокируются через pytest-mock (unittest.mock).
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.schedule_parser import _parse_html, fetch_group_schedule, clear_schedule_cache

SAMPLE_HTML = """
<html><body>
<h1>Расписание группы ВЦ25-01</h1>
<table>
  <tr><td colspan="4">Понедельник</td></tr>
  <tr>
    <td>1</td>
    <td>08:30-10:05</td>
    <td>Математика лек.<br>
        <a href="?teacher=Кнауб+Л.+В.">Кнауб Л. В.</a><br>
        Корпус №80, ауд. 4-06
    </td>
    <td></td>
  </tr>
  <tr>
    <td>3</td>
    <td>12:00-13:35</td>
    <td></td>
    <td>Программирование лаб.<br>
        <a href="?teacher=Иванов+И.+И.">Иванов И. И.</a><br>
        Корпус №5, ауд. 1-01
    </td>
  </tr>
</table>
</body></html>
"""


def test_parse_html_title():
    result = _parse_html(SAMPLE_HTML)
    assert result["title"] == "Расписание группы ВЦ25-01"


def test_parse_html_lessons():
    result = _parse_html(SAMPLE_HTML)
    lessons = result["lessons"]
    assert len(lessons) >= 1
    lesson = lessons[0]
    assert lesson["day"] == "Понедельник"
    assert lesson["period"] == 1
    assert lesson["week_type"] == "odd"
    assert "Математика" in lesson["subject"]
    assert lesson["teacher"] == "Кнауб Л. В."
    assert "80" in lesson["location"] or "ауд" in lesson["location"]


def test_parse_html_lab():
    result = _parse_html(SAMPLE_HTML)
    labs = [l for l in result["lessons"] if l["type"] == "lab"]
    assert len(labs) >= 1
    assert labs[0]["week_type"] == "even"


@pytest.mark.asyncio
async def test_fetch_group_schedule_uses_cache():
    clear_schedule_cache()
    mock_response = MagicMock()
    mock_response.text = SAMPLE_HTML
    mock_response.raise_for_status = MagicMock()

    with patch("app.services.schedule_parser.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        result1 = await fetch_group_schedule("ВЦ25-01")
        result2 = await fetch_group_schedule("ВЦ25-01")  # должен вернуться из кеша

    # get вызван только один раз (второй запрос — из кеша)
    assert mock_client.get.call_count == 1
    assert result1["title"] == result2["title"]


@pytest.mark.asyncio
async def test_clear_cache():
    clear_schedule_cache()
    mock_response = MagicMock()
    mock_response.text = SAMPLE_HTML
    mock_response.raise_for_status = MagicMock()

    with patch("app.services.schedule_parser.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        await fetch_group_schedule("ВЦ25-01")
        count = clear_schedule_cache()
        assert count >= 1
