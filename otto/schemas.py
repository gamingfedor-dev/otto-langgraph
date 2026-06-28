from pydantic import BaseModel


class Decision(BaseModel):
    next: str
    reason: str
