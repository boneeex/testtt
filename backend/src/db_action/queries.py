from sqlalchemy import select, insert, and_, delete, update
from sqlalchemy.orm import selectinload
import datetime


from src.database import async_session_factory as asf
from .models import TeachersOrm, TaskOrm, TestsOrm, CommentsOrm, SessionOrm, IsStarted, UserOrm
from src.schemas.router_db import TeacherRegister
from src.schemas.from_dbDTO import TeacherInfo, Comments, TaskInfo, Tests, SessionInfo, CompetetorsList, OverviewStartedSession
from src.utils import PasswordActions, generate_unique_code
from src.schemas.from_dbDTO import list_of_tasks


class Users:
    @staticmethod
    async def register_teacher(teacher_info: TeacherRegister):
        async with asf() as session:
            new_teacher = TeachersOrm(
                name=teacher_info.name,
                email=teacher_info.email,
                password_hash=PasswordActions.hash(teacher_info.password)
            )
            session.add(new_teacher)
            await session.commit()  


    @staticmethod
    async def check_teacher_uniqueness_and_return_password(teacher_email: str):
        async with asf() as session:
            query = select(TeachersOrm.password_hash).where(TeachersOrm.email == teacher_email)
            result = await session.execute(query)
            return result.scalar_one_or_none()
    

    @staticmethod
    async def list_of_tasks():
        async with asf() as session:
            query = select(TaskOrm.title, TaskOrm.time_created)
            result = await session.execute(query)
            return [list_of_tasks(title=title, time_created=time_created) for title, time_created in result]
    

    @staticmethod
    async def get_teacher_info_by_email(teacher_email: str) -> TeacherInfo:
        async with asf() as session:
            query = select(TeachersOrm.id, TeachersOrm.name).where(TeachersOrm.email == teacher_email)
            result = await session.execute(query)
            return [TeacherInfo(id=id, name=name) for id, name in result]
        

    @staticmethod
    async def create_task_return_task_id(title: str, task_text: str, teacher_id: int):
        async with asf() as session:
            query = insert(TaskOrm).values(title=title, task_text=task_text, teacher_fk=teacher_id)
            await session.execute(query)
            await session.flush()
            query = select(TaskOrm.id).where(and_(TaskOrm.title == title))
            result = await session.execute(query)
            await session.commit()
            return result.scalar_one_or_none()
        
    
    @staticmethod
    async def add_tests_to_task(list_of_tests: list, task_id: int):
        async with asf() as session:
            tests = [TestsOrm(input=test.input, output=test.output, task_fk=task_id) for test in list_of_tests]
            await session.add_all(tests)
            await session.commit()

    
    @staticmethod
    async def view_task_info(task_id: int):
        async with asf() as session:
            query = select(TaskOrm).options(
                selectinload(TaskOrm.teacher),  # Load teacher for the task
                selectinload(TaskOrm.tests),    # Load all tests
                selectinload(TaskOrm.comments).selectinload(CommentsOrm.teacher)  # Load comments and each comment's teacher
            ).where(TaskOrm.id == task_id)
            
            result = await session.execute(query)
            task = result.scalar_one_or_none()
            
            if task is None:
                return None  # or raise an exception if preferred

            # Map ORM task to TaskInfo pydantic model
            task_info = TaskInfo(
                title=task.title,
                task_text=task.task_text,
                time_created=str(task.time_created),  # Convert datetime to str if needed
                teacher_name=task.teacher.name
            )
            
            # Map each test to the Tests pydantic model
            tests = [
                Tests(
                    input=test.input,
                    output=test.output,
                    input_type=type(test.input).__name__,
                    output_type=type(test.output).__name__
                ) for test in task.tests
            ]
            
            # Map each comment to the Comments pydantic model
            comments = [
                Comments(
                    text=comment.text,
                    time_created=str(comment.time_created),  # Converting datetime to str if needed
                    teacher_name=comment.teacher.name
                ) for comment in task.comments
            ]
            
            return {"task_info": task_info, "tests": tests, "comments": comments}
        
    @staticmethod
    async def delete_task(task_id: int):
        async with asf() as session:
            query = delete(TaskOrm).where(TaskOrm.id == task_id)
            await session.execute(query)
            await session.commit()

    #update
    @staticmethod
    async def update_task_title(task_id: int, content: str):
        async with asf() as session:
            query = update(TaskOrm.title).where(TaskOrm.id == task_id).values(content)
            await session.execute(query)
            await session.commit()


    @staticmethod
    async def update_task_text(task_id: int, content: str):
        async with asf() as session:
            query = update(TaskOrm.task_text).where(TaskOrm.id == task_id).values(content)
            await session.execute(query)
            await session.commit()

    
    @staticmethod
    async def leave_comment(teacher_id: int, task_id: int, comment: str):
        async with asf() as session:
            query = insert(CommentsOrm).values(text=comment, task_fk=task_id, teacher_fk=teacher_id)
            await session.execute(query)
            await session.commit()

    
    #session
    @staticmethod
    async def create_session(teacher_id: int, task_id: int, deadline_time: datetime.datetime):
        async with asf() as session:
            unique_code = generate_unique_code()
            query = insert(SessionOrm).values(deadline_time=deadline_time,
                                              task_fk=task_id, teacher_fk=teacher_id, 
                                              unique_code=unique_code)
            await session.execute(query)
            await session.commit()

    
    @staticmethod
    async def look_for_teacher_session_and_return_unique_code(teacher_id: int):
        async with asf() as session:
            query = select(SessionOrm.unique_code).where(SessionOrm.teacher_fk == teacher_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()
        

    @staticmethod
    async def get_session_info_by_id(id: int):
        async with asf() as session:
            query = select(SessionOrm).where(SessionOrm.id == id)
            result = await session.execute(query)
            query = select(UserOrm)
            return SessionInfo(**result.scalars())
        

    @staticmethod
    async def session_change_status(session_id: int, status: IsStarted):
        async with asf() as session:
            query = update(SessionOrm).where(SessionOrm.id == session_id).values(status=status)
            await session.execute(query)
            await session.commit()
        

    @staticmethod
    async def get_session_info_by_unique_code(unique_code: str):
        async with asf() as session:
            query = select(SessionOrm).where(SessionOrm.unique_code == unique_code)
            result = await session.execute(query)
            session_info = SessionInfo(**result.scalars())
            query = select(UserOrm.name).where(UserOrm.session_fk == session_info.id)
            result = await session.execute(query)
            users = [CompetetorsList(name=name) for name in result.scalars()]
            return OverviewStartedSession(session_info=session_info, competetors_list=users)   