import os
import sys
import asyncio
from fastapi import FastAPI
import uvicorn

sys.path.insert(1, os.path.join(sys.path[0], '..'))

from backend.src.utils import create_tables
from src.routers.teacher import teacher_router
from src.routers.user import user_router



app = FastAPI()

app.include_router(teacher_router)
app.include_router(user_router)



if __name__ == '__main__':
    async def main():
        await create_tables()
        config = uvicorn.Config(app, host="127.0.0.1", port=8000)
        server = uvicorn.Server(config)
        await server.serve()
    
    asyncio.run(main())
    