from dataclasses import dataclass

from zozode.constants import DIFFICULTY_EASY, DIFFICULTY_HARD

DEFAULT_PORT = 2806


@dataclass(frozen=True, slots=True)
class UdpConfig:
    host: str = "127.0.0.1"
    port: int = DEFAULT_PORT
    buffer_size: int = 65_507
    encoding: str = "utf-8"

    def address(self) -> tuple[str, int]:
        return self.host, self.port

    def validate(self) -> None:
        if not 1 <= self.port <= 65_535:
            msg = f"port must be between 1 and 65535, got {self.port}"
            raise ValueError(msg)
        if self.buffer_size <= 0:
            msg = f"buffer_size must be positive, got {self.buffer_size}"
            raise ValueError(msg)


def validate_difficulty(value: int) -> int:
    if not DIFFICULTY_EASY <= value <= DIFFICULTY_HARD:
        msg = f"difficulty must be 0, 1, or 2, got {value}"
        raise ValueError(msg)
    return value
