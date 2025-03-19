from pydantic import BaseModel
from typing import List

from .incoming import Tests


class list_of_tasks(BaseModel):
    title: str
    time_created: str


class TeacherInfo(BaseModel):
    id: int
    name: str

#/view_task_info
class TaskInfo(BaseModel):
    title: str
    task_text: str
    time_created: str
    teacher_name: str


class Tests(BaseModel):
    input: str | int | float | bool
    output: str | int | float | bool
    input_type: str
    output_type: str


class Comments(BaseModel):
    text: str
    time_created: str
    teacher_name: str
    

class SessionInfo(BaseModel):
    id: int
    deadline_time: str
    status: str
    unique_code: str
    teacher_fk: int


class CompetetorsList(BaseModel):
    name: str 


class OverviewStartedSession(BaseModel):
    session_info: SessionInfo
    competetors_list: List[CompetetorsList]


#users 
class UserOrm(BaseModel):
    name: str

# class Tests(BaseModel):
#     input: str | int | float | bool
#     output: str | int | float | bool

class UserTestResult(Tests):
    user_output: str | int | float | bool


class UserOverviewResult(BaseModel):
    name: str
    test_results: List[UserTestResult]