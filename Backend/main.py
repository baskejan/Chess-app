#Aqui es donde voy a crear todos mis endpoints
import os 
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import create_db_and_tables, get_session
from contextlib import asynccontextmanager
from models.user import User
from routers import api_router
import pandas as pd
import asyncio
from routers.matchmaking import manager
from routers.GameManager import game_manager

load_dotenv()
FRONT_PORT = os.getenv("FRONT_PORT")

#Definamos la funcion de Lifespan que controla que se hace antes y despues de iniciar la app
@asynccontextmanager
async def lifespan(app: FastAPI):
    #Debo de crear las tablas
    create_db_and_tables()
    #Creamos el MatchMakingManager
    asyncio.create_task(manager.TimeOutWorker())
    asyncio.create_task(manager.MatchMakingWorker())
    asyncio.create_task(game_manager.CreateGame())
    yield
    print("Sea ha apagado el sistema")

#Esto crea la Instancia de mi app
app = FastAPI(lifespan=lifespan)


#Definimos un Middleware
origins = [
    "*"  
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,             # 2. Los dominios que permitimos
    allow_credentials=False,            # 3. Permitir cookies, headers de autorización, etc.
    allow_methods=["*"],               # 4. Permitir todos los métodos (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],               # 5. Permitir todos los encabezados (como Content-Type)
)
app.include_router(api_router)




