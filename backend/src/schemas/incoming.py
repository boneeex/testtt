from pydantic import BaseModel, Field

class TaskCreation(BaseModel):
    title: str = Field(min_length=1, max_length=50)
    text: str = Field(min_length=1, max_length=500)


class Tests(BaseModel):
    input: str | int | float | bool
    output: str | int | float | bool