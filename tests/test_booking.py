"""Три автотеста формы бронирования: позитивный, негативный и проверка дефекта."""

from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

from conftest import Spec
from pages.booking_page import BookingData, BookingPage

FIELDS = ("room", "date", "startTime", "endTime", "participants", "name", "email")
XSS_PAYLOAD = "<img src=xxx onerror=alert('XSS')>"
EVIDENCE_PATH = "artifacts/evidence/BUG-01-name-xss.png"


@pytest.mark.regression
def test_successful_booking(
    booking_page: BookingPage, valid_booking: BookingData, spec: Spec
) -> None:
    """Позитивный сценарий: корректное заполнение показывает подтверждение брони."""
    booking_page.open()
    booking_page.submit_booking(valid_booking)

    expected_parts = (
        spec.status_success,
        spec.ROOMS[valid_booking.room],
        valid_booking.date,
        f"{valid_booking.start_time}–{valid_booking.end_time}",
        valid_booking.name,
    )

    expect(booking_page.status).to_have_class("form-status success")
    for part in expected_parts:
        expect(booking_page.status).to_contain_text(part, use_inner_text=True)

    for name in FIELDS:
        expect(booking_page.error_for(name)).to_be_empty()
        expect(booking_page.field(name)).not_to_have_class("has-error")


@pytest.mark.regression
def test_invalid_booking(
    booking_page: BookingPage, valid_booking: BookingData, spec: Spec
) -> None:
    """Негативный сценарий: участников больше вместимости выбранной комнаты."""
    data = valid_booking.with_(room="small", participants="5")
    booking_page.open()
    booking_page.submit_booking(data)

    participants_input = booking_page.input("participants")
    capacity = booking_page.capacity_of(data.room)
    assert int(participants_input.get_attribute("min")) == spec.PARTICIPANTS_MIN
    assert int(participants_input.get_attribute("max")) == spec.PARTICIPANTS_MAX
    assert capacity == spec.CAPACITIES[data.room]

    expect(booking_page.error_for("participants")).to_have_text(
        spec.capacity_error(data.room)
    )
    expect(booking_page.field("participants")).to_have_class("field has-error")
    expect(booking_page.status).to_have_class("form-status error")
    expect(booking_page.status).to_contain_text(spec.status_error)
    expect(booking_page.status).not_to_contain_text(spec.status_success)
    expect(booking_page.status).not_to_contain_text(spec.ROOMS[data.room])


@pytest.mark.security
@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="BUG-01: В поле имени можно ввести xss-инъекцию",
)
def test_discovered_defect(
    booking_page: BookingPage, valid_booking: BookingData, spec: Spec
) -> None:
    """Проверка дефекта BUG-01: проверяется корректное ожидаемое поведение —
    пользовательский ввод является данными, а не разметкой."""
    dialogs: list[str] = []
    booking_page.page.on("dialog", lambda dialog: (dialogs.append(dialog.message), dialog.dismiss()))

    data = valid_booking.with_(name=XSS_PAYLOAD)
    booking_page.open()
    booking_page.submit_booking(data)

    evidence = Path(EVIDENCE_PATH)
    evidence.parent.mkdir(parents=True, exist_ok=True)
    booking_page.page.screenshot(path=str(evidence))

    expect(booking_page.status).to_have_class("form-status success")
    expect(booking_page.status).to_contain_text(spec.status_success)
    expect(booking_page.status).to_contain_text(XSS_PAYLOAD, use_inner_text=True)
    expect(booking_page.status.locator("img")).to_have_count(0)
    # Диалог появляется асинхронно после onerror: сначала web-first ожидание
    # (оно же является доказательством DOM-инъекции), затем факт диалога.
    booking_page.page.wait_for_timeout(1000)
    assert not dialogs, "alert() был исполнен — payload обработан как разметка"
