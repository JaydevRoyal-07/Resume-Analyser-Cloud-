from typing import Optional
from pydantic import BaseModel

class UserIn(BaseModel):
    name: str
    email: str
    password: str

class UserOut(BaseModel):
    id: str
    name: str
    email: str
    role: Optional[str] = "hr"
