from pydantic import BaseModel
from typing import Optional

class GenreCreate(BaseModel):
    id: int
    name: str
    slug: str

class TagUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    games_count: Optional[int] = None
    image_background: Optional[str] = None
    score: Optional[float] = None


