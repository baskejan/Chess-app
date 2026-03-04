from sqlmodel import SQLModel, Field
from pydantic import EmailStr



#Primer Modelo de Tabla de Usuario
class User(SQLModel, table= True):
    id: int | None = Field(default=None, primary_key=True)
    user_name: str = Field(default=str, unique=True)
    hashed_password: str
    email: EmailStr = Field(default=EmailStr, unique=True)

#Modelo de Usuario a la hora del envio de informacion al Endpoint Login
class UserLogin(SQLModel):
    user_name: str
    password: str

#Modelo de Usuario a la hora del envio de informacion al Endpoint SignUp

class UserSignUp(SQLModel):
    user_name: str
    password: str
    email: EmailStr







