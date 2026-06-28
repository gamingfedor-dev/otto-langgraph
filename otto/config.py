from dataclasses import dataclass


@dataclass
class OttoConfig:
    model: str | None = None
    max_turns: int = 6
    max_specialists: int = 5
    recursion_limit: int = 25
    retry_attempts: int = 3
    persist: bool = False
