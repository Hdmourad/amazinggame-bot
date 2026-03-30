"""Time-based animation helpers for viewer values."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

_date_offset: float = 0


def date() -> float:
    """Return synchronized current time used by viewer animations."""
    return perf_counter() + _date_offset


def set_date(server_date: float) -> None:
    """Initialize viewer/server time offset once from server timestamp."""
    global _date_offset  # noqa:  PLW0603
    if _date_offset == 0:
        _date_offset = server_date - perf_counter()


class Animation:
    """Represents one linear value transition over time."""

    def __init__(
        self,
        start_value: float,
        end_value: float,
        duration: float = 1.0,
        start_time: float | None = None,
    ) -> None:
        """Create an animation segment with start/end values and timing."""
        self.duration = duration
        if start_time is None:
            self.start_time = date()
        else:
            self.start_time = start_time
        self.start_value = start_value
        self.end_value = end_value

    @property
    def end_time(self) -> float:
        """Return time when this animation segment ends."""
        return self.start_time + self.duration

    def value(self, time: float) -> int:
        """Return interpolated value at the provided time."""
        factor = (time - self.start_time) / self.duration
        return int(self.start_value + (self.end_value - self.start_value) * factor)


@dataclass
class Step:
    """Describes one target value and duration step in a sequence."""

    duration: float
    value: float


class AnimatedValue:
    """Holds and evaluates queued animation segments for a value."""

    def __init__(self, initial_value: int = 0) -> None:
        """Initialize animated value with an optional starting value."""
        self._animations: list[Animation] = []
        self._last_value = initial_value

    def __len__(self) -> int:
        """Return number of queued animation segments."""
        return len(self._animations)

    @property
    def value(self) -> float:
        """Return current value after advancing active animations."""
        current_time = date()
        to_be_removed = []
        for animation in self._animations:
            if animation.end_time < current_time:
                self._last_value = animation.end_value
                to_be_removed.append(animation)  # already finished
                continue
            if animation.start_time > current_time:
                continue  # not yet started
            self._last_value = animation.value(current_time)
        for animation in to_be_removed:
            self._animations.remove(animation)
        return self._last_value

    def add_animation(self, animation: Animation) -> None:
        """Append a single animation segment."""
        self._animations.append(animation)

    def add_animations(
        self,
        initial_value: float,
        steps: list[Step],
        start_time: float | None = None,
    ) -> None:
        """Append a sequence of animation steps starting at initial_value."""
        if not steps:
            return
        self._animations.append(
            Animation(
                start_value=initial_value,
                start_time=start_time,
                end_value=steps[0].value,
                duration=steps[0].duration,
            )
        )
        for step in steps[1:]:
            last_animation = self._animations[-1]
            self._animations.append(
                Animation(
                    start_value=last_animation.end_value,
                    start_time=last_animation.end_time,
                    end_value=step.value,
                    duration=step.duration,
                )
            )
