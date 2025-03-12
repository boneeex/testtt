from fastapi import APIRouter, Form, HTTPException, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from typing import Annotated
import datetime
import logging

from src.db_action.models import IsStarted
from src.schemas.router_db import TeacherRegister, JWTSchema
from src.schemas.incoming import Tests, TaskCreation
from src.db_action.queries import Users
from backend.src.utils import PasswordActions, JWTActions, AuthActions


teacher_router = APIRouter(prefix="/teachers")
not_authorized = HTTPException(status_code=401, detail="Пользователь не авторизован")


@teacher_router.post("/register")
async def teacher_login(name: Annotated[str, Form()], email: Annotated[str, Form()], password: Annotated[str, Form()]):
    try:
        new_teacher = TeacherRegister(name=name, email=email, password=password)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail="Не валидные данные")
    
    await Users.register_teacher(new_teacher)
    return JSONResponse(content={"message": "Пользователь успешно зарегистрирован"})
    # except Exception as e:
    #     print(e)
    #     raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")


@teacher_router.post("/login")
async def teacher_login(email: Annotated[str, Form()], password: Annotated[str, Form()]):
    password_hash = await Users.check_teacher_uniqueness_and_return_password(email)
    if password_hash:
        if PasswordActions.validate(password=password, hashed_password=password_hash):
            payload  = {"sub": email}
            token = JWTActions.encode(payload=payload)
            return JWTSchema(access_token=token, token_type="Bearer")
        else:
            raise HTTPException(status_code=400, detail="Неверный пароль")
    else:
        raise HTTPException(status_code=404, detail="Пользователь с такой почтой не найден")
    

@teacher_router.get("/teacher_mainpage")
async def teacher_mainpage(token: Annotated[str, Depends(AuthActions.oauth2_scheme)]):
    if await AuthActions.validate_user(token=token):
        list_of_tasks = await Users.list_of_tasks()
        return list_of_tasks
    return not_authorized


@teacher_router.post("/create_task")
async def create_task(token: Annotated[str, Depends(AuthActions.oauth2_scheme)],
                      title: Annotated[str, Form()],
                      text: Annotated[str, Form()],
                      list_of_tasks: list = Annotated[Tests, Form()],
                      ):
    if await AuthActions.validate_user(token=token):
        #проверяем валидность ввода текста для задания
        try:
            TaskCreation(title=title, task_text=text)
        except:
            raise HTTPException(status_code=400, detail="Неккоректный ввод")

        teacher_info = await Users.get_teacher_info_by_email(token=token)
        #вносим в бд новое задание + тесты к нему в таблицу tests
        try:
            task_id = await Users.create_task_return_task_id(title=title, task_text=text, teacher_id=teacher_info.id)
            await Users.add_tests_to_task(list_of_tests=list_of_tasks, task_id=task_id)
            return JSONResponse(content={"message": "Задание успешно создано"})
        except:
            raise HTTPException(status_code=400, detail="Неккоректный ввод")
    return not_authorized


@teacher_router.get("/view_task_info")
async def view_task_info(token: Annotated[str, Depends(AuthActions.oauth2_scheme)], task_id: int):
    if await AuthActions.validate_user(token=token):
        task_info = await Users.view_task_info(task_id=task_id)
        return JSONResponse(status_code=200, content=task_info)
    return not_authorized


@teacher_router.delete("/delete_task")
async def delete_task(token: Annotated[str, Depends(AuthActions.oauth2_scheme)], task_id: int):
    if await AuthActions.validate_user(token=token):
        try:
            await Users.delete_task(task_id=task_id)
            return JSONResponse(status_code=201, 
                                content={"message": f"Задание успешно удалено c id {task_id} успешно удалено"}) 
        except:
            raise HTTPException(status_code=404, detail="Задания не существует")
    return not_authorized


@teacher_router.put("/update_task")
async def update_task(token: Annotated[str, Depends(AuthActions.oauth2_scheme)], task_change: dict, task_id: int):
    if await AuthActions.validate_user(token=token):
        try: 
            title = task_change["title"]
            await Users.update_task_title(task_id=task_id, content=title) 
            return JSONResponse(status_code=200, content={"message": "Название задания успешно обновлено"})
        except:
            task_text = task_change["task_text"]
            await Users.update_task_text(task_id=task_id, content=task_text)
            return JSONResponse(status_code=200, content={"message": "Текст задания успешно обновлен"})
    return not_authorized


@teacher_router.post("/leave_comment")
async def view_tasks(token: Annotated[str, Depends(AuthActions.oauth2_scheme)], task_id: int, comment: Annotated[str, Form()]):
    if await AuthActions.validate_user(token=token):
        try:
            teacher_id = await Users.get_teacher_info_by_email(token=token)
            await Users.leave_comment(teacher_id=teacher_id.id, task_id=task_id, comment=comment)
        except:
            raise HTTPException(status_code=500, detail="Что-то пошло не так")    
        return JSONResponse(status_code=200, content={"message": "Комментарии успешно отправлены"})
    return not_authorized


@teacher_router.post("/create_session")
async def create_session(token: Annotated[str, Depends(AuthActions.oauth2_scheme)], task_id: int, deadline_time: Annotated[datetime.datetime, Form()]):
    if await AuthActions.validate_user(token=token):
        teacher_id = await Users.get_teacher_info_by_email(token=token).id
        probable_unique_code = await Users.look_for_teacher_session(teacher_id=teacher_id)
        if await probable_unique_code:
            raise HTTPException(status_code=400,
                                detail=f"У вас уже есть активная сессия доступная по ссылке http://127.0.0.1:8000/teacher/session_preview{probable_unique_code}")
        await Users.create_session(teacher_id=teacher_id, task_id=task_id, deadline_time=deadline_time)
        return JSONResponse(status_code=200, content={"message": "Сессия успешно создана"})
    return not_authorized


@teacher_router.get("/session_preview/{unique_code}")
async def view_session_info(token: Annotated[str, Depends(AuthActions.oauth2_scheme)], session_id: int):
    if await AuthActions.validate_user(token=token):
        teacher_info = await Users.get_teacher_info_by_email(token=token)
        teachers_session = await Users.look_for_teacher_session_and_return_unique_code(teacher_id=teacher_info.id)
        session_info = await Users.view_session_info(session_id=session_id)
        if session_info.unique_code == teachers_session:
            return Users.get_session_info_by_id(id=session_id)
        return HTTPException(status_code=403, detail="Сессия создана не вами")
    return not_authorized


@teacher_router.post("/session_preview/{unique_code}")
async def start_session(token: Annotated[str, Depends(AuthActions.oauth2_scheme)], session_id: int):
    if await AuthActions.validate_user(token=token):
        teacher_info = await Users.get_teacher_info_by_email(token=token)
        teachers_session = await Users.look_for_teacher_session_and_return_unique_code(teacher_id=teacher_info.id)
        session_info = await Users.view_session_info(session_id=session_id)
        if session_info.unique_code == teachers_session:
            await Users.session_change_status(session_id=session_id, status=IsStarted.started)
            return RedirectResponse(url=f"http://127.0.0.1:8000/teacher/started_session_info/{teachers_session}")
        return HTTPException(status_code=403, detail="Сессия создана не вами")
    return not_authorized


@teacher_router.get("/started_session_info/{unique_code}")
async def view_session_info(token: Annotated[str, Depends(AuthActions.oauth2_scheme)], unique_code: str):
    if await AuthActions.validate_user(token=token):
        teacher_info = await Users.get_teacher_info_by_email(token=token)
        if await Users.look_for_teacher_session_and_return_unique_code(teacher_id=teacher_info.id) == unique_code:
            session_overview = Users.get_session_info_by_unique_code(unique_code=unique_code)
            return JSONResponse(status_code=200, content=session_overview)
        return HTTPException(status_code=403, detail="Сессия создана не вами")
    return not_authorized


@teacher_router.post("/end_session/{unique_code}")
async def end_session(token: Annotated[str, Depends(AuthActions.oauth2_scheme)], unique_code: str):
    if await AuthActions.validate_user(token=token):
        teacher_info = await Users.get_teacher_info_by_email(token=token)
        if await Users.look_for_teacher_session_and_return_unique_code(teacher_id=teacher_info.id) == unique_code:
            session_overview = Users.get_session_info_by_unique_code(unique_code=unique_code)
            await Users.session_change_status(session_id=session_overview.id, status=IsStarted.finished)
            return JSONResponse(status_code=200, content=session_overview)
        return HTTPException(status_code=403, detail="Сессия создана не вами")
    return not_authorized


@teacher_router.post("/view_session_results/{unique_code}")
async def view_session_results(token: Annotated[str, Depends(AuthActions.oauth2_scheme)], unique_code: str):
    return not_authorized