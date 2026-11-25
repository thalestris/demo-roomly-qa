from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date

from playwright.sync_api import Page


@dataclass(frozen=True)
class BookingData:
    room: str
    date: str
    start_time: str
    end_time: str
    participants: str
    name: str
    email: str

    def with_(self, **changes: str) -> "BookingData":
        return replace(self, **changes)


class BookingPage:

    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url


    def open(self) -> None:
        response = self.page.goto(self.base_url)
        if response is None or not response.ok:
            raise RuntimeError(f"Страница недоступна: {self.base_url}")

    def browser_today(self) -> date:
        iso = self.page.evaluate(
            "() => new Date(Date.now() - new Date().getTimezoneOffset() * 60000)"
            ".toISOString().slice(0, 10)"
        )
        return date.fromisoformat(iso)

    def fill(self, data: BookingData) -> None:
        self.page.select_option("#room", data.room)
        self.page.fill("#date", data.date)
        self.page.fill("#start-time", data.start_time)
        self.page.fill("#end-time", data.end_time)
        self.page.fill("#participants", data.participants)
        self.page.fill("#name", data.name)
        self.page.fill("#email", data.email)

    def submit(self) -> None:
        self.submit_button.click()

    def submit_booking(self, data: BookingData) -> None:
        self.fill(data)
        self.submit()

    @property
    def status(self):
        return self.page.get_by_role("status")

    @property
    def submit_button(self):
        return self.page.get_by_role("button", name="Забронировать")

    def input(self, name: str):
        return self.page.locator(f'[name="{name}"]')

    def field(self, name: str):
        return self.page.locator(f'.field:has([name="{name}"])')

    def error_for(self, name: str):
        return self.page.locator(f'.field-error[data-error-for="{name}"]')

    def capacity_of(self, room: str) -> int:
        value = self.page.locator(f'#room option[value="{room}"]').get_attribute(
            "data-capacity"
        )
        if value is None:
            raise RuntimeError(f"Для комнаты {room} нет атрибута data-capacity")
        return int(value)
