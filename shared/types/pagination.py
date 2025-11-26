from pydantic import BaseModel


class Pagination(BaseModel):
    first: int
    rows: int
    total: int
