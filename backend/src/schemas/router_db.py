from pydantic import BaseModel, Field, EmailStr


class TeacherRegister(BaseModel):
    name: str = Field(min_length=1, max_length=30)
    email: EmailStr = Field(min_length=1, max_length=40)
    password: str = Field(min_length=8, max_length=30)
    

class TeacherAuth(BaseModel):
    email: EmailStr
    password: str

class JWTSchema(BaseModel):
    access_token: str
    token_type: str