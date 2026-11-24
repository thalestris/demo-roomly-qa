"""Фикстуры автотестов формы бронирования.

Ожидания (Spec) — это формулировки из требований (README), а не копия текста из
script.js: тест сверяет спецификацию с реализацией. Факты о границах полей
(вместимость, min/max) читаются из разметки страницы через Page Object,
поэтому числа в тестах не дублируются.
"""
from __future__ import annotations

import os
from datetime import timedelta

import pytest

from pages.booking_page import BookingData, BookingPage


@pytest.fixture(scope="session")
def base_url(pytestconfig):
    """CLI --base-url takes precedence over BASE_URL and the demo address."""
    return (
        pytestconfig.getoption("--base-url")
        or os.environ.get("BASE_URL")
        or "https://rcsi-science.github.io/demo-roomly/"
    )


def plural(count: int, one: str, few: str, many: str) -> str:
    """Форма существительного по правилу русского языка."""
    n = abs(count) % 100
    if 11 <= n <= 14:
        return many
    last = n % 10
    if last == 1:
        return one
    if 2 <= last <= 4:
        return few
    return many


class Spec:
    """Ожидаемое поведение формы из раздела «Ожидаемое поведение» README."""

    ROOMS = {"small": "Малая", "medium": "Средняя", "large": "Большая"}
    CAPACITIES = {"small": 4, "medium": 10, "large": 20}
    PARTICIPANTS_MIN = 1
    PARTICIPANTS_MAX = 20

    status_success = "Бронирование создано."
    status_error = "Проверьте, пожалуйста, заполнение формы."

    def capacity_error(self, room: str) -> str:
        capacity = self.CAPACITIES[room]
        return (
            f"В комнате максимум {capacity} "
            f"{plural(capacity, 'участник', 'участника', 'участников')}."
        )

    def participants_range_error(self) -> str:
        return (
            f"Количество участников — от {self.PARTICIPANTS_MIN} до "
            f"{self.PARTICIPANTS_MAX}."
        )


@pytest.fixture(scope="session")
def spec() -> Spec:
    return Spec()


@pytest.fixture
def booking_page(page, base_url: str) -> BookingPage:
    """Function-scoped: изолированная страница на каждый тест."""
    return BookingPage(page, base_url)


@pytest.fixture
def valid_booking(booking_page: BookingPage, spec: Spec) -> BookingData:
    """Корректный набор данных: комната, которая его принимает."""
    room = "medium"
    return BookingData(
        room=room,
        date=(booking_page.browser_today() + timedelta(days=7)).isoformat(),
        start_time="10:00",
        end_time="11:30",
        participants="6",  # тестовые данные: меньше вместимости выбранной комнаты
        name="Anna Petrova",
        email="anna.petrova@company.ru",
    )
