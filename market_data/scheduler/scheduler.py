import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
import traceback
from typing import Callable
from zoneinfo import ZoneInfo


@dataclass(slots=True)
class ScheduledJob:
    name: str
    interval_seconds: int
    callback: Callable[[], None]
    boundary_minutes: int | None = None


class Scheduler:
    def __init__(self):
        self._jobs: list[ScheduledJob] = []
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def add_job(
        self,
        name: str,
        interval_seconds: int,
        callback: Callable[[], None],
    ) -> None:
        self._jobs.append(
            ScheduledJob(
                name=name,
                interval_seconds=interval_seconds,
                callback=callback,
            )
        )

    def add_boundary_job(
        self,
        name: str,
        minutes: int,
        callback: Callable[[], None],
    ) -> None:
        if minutes <= 0 or 60 % minutes != 0:
            raise ValueError(
                "minutes must be a positive divisor of 60"
            )

        self._jobs.append(
            ScheduledJob(
                name=name,
                interval_seconds=minutes * 60,
                callback=callback,
                boundary_minutes=minutes,
            )
        )

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            raise RuntimeError("Scheduler is already running")

        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._run,
            name="scheduler",
            daemon=True,
        )

        self._thread.start()

        print("Scheduler started")

    def stop(self) -> None:
        self._stop_event.set()

        if self._thread is not None:
            self._thread.join(timeout=5)

        print("Scheduler stopped")

    def _run(self) -> None:
        next_run: dict[str, float] = {}

        for job in self._jobs:
            if job.boundary_minutes is not None:
                next_run[job.name] = self._next_boundary_timestamp(
                    job.boundary_minutes
                )
            else:
                next_run[job.name] = (
                    time.monotonic()
                    + job.interval_seconds
                )

        while not self._stop_event.is_set():

            now = time.monotonic()

            for job in self._jobs:
                if now >= next_run[job.name]:
                    try:
                        print(
                            f"Running scheduled job: {job.name}"
                        )
                        job.callback()

                    except Exception as e:
                        print(
                            f"ERROR in scheduled job "
                            f"{job.name}: {e}"
                        )
                        traceback.print_exc()

                    if job.boundary_minutes is not None:
                        next_run[job.name] = (
                            self._next_boundary_timestamp(
                                job.boundary_minutes
                            )
                        )
                    else:
                        next_run[job.name] = (
                            time.monotonic()
                            + job.interval_seconds
                        )

            self._stop_event.wait(0.5)

    @staticmethod
    def _next_boundary_timestamp(minutes: int) -> float:
        now = datetime.now().astimezone()

        current_minute = now.minute

        next_minute = (
            (current_minute // minutes + 1) * minutes
        )

        if next_minute >= 60:
            boundary = (
                now.replace(
                    minute=0,
                    second=0,
                    microsecond=0,
                )
                + timedelta(hours=1)
            )
        else:
            boundary = now.replace(
                minute=next_minute,
                second=0,
                microsecond=0,
            )

        delay = (
            boundary - now
        ).total_seconds()

        return time.monotonic() + delay