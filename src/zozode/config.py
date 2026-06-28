from dataclasses import dataclass

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
