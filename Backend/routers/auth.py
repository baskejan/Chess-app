from fastapi import APIRouter, Depends
from models.user import User, UserSignUp, UserLogin
from database import get_session
from sqlmodel import Session, select
from fastapi import APIRouter
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi import status
import bcrypt


#Funciones para autenticar
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

#Instancia del Router
router = APIRouter(prefix= "/users")

#Endopint para crear un nuevo usuario
@router.post("/signup", status_code=status.HTTP_201_CREATED)
def create_user(InfoUser: UserSignUp, session: Session = Depends(get_session)):
    #1. Revisar sí el nombre de usuario ya existe
    statement1 = select(User).where(User.user_name == InfoUser.user_name)

    #2. Revisar que la cuenta de correo ya tenga un usuario existente

    statement2 = select(User).where(User.email == InfoUser.email)

    ExtractedUser1 = session.exec(statement=statement1).first()
    ExtractedUser2 = session.exec(statement=statement2).first()

    if ExtractedUser1:
        raise HTTPException(status_code=400, detail="Usuario ya existente")
    
    elif ExtractedUser2:
        raise HTTPException(status_code=400, detail= "Correo ya registrado")
    
    #2. Hashear la contraseña
    hashed_password = hash_password(InfoUser.password)

    #3. Crear el Usuario a Ingresar
    NewUser = User(user_name=InfoUser.user_name, hashed_password=hashed_password, email= InfoUser.email)
    
    #4. Introducir el Usuario a la Base de Datos
    session.add(NewUser)
    session.commit()
    session.refresh(NewUser)
    return {"detail": "Usuario creado exitosamente"}

#Endpoint para poder extraer la información del usuario
@router.post("/login", status_code=status.HTTP_202_ACCEPTED)
def confirmar_usuario(LoginUser: UserLogin, session: Session = Depends(get_session)):
    #1. Debo buscar el Usuario en la base de datos
    statement = select(User).where(User.user_name == LoginUser.user_name)
    ExtractedUser = session.exec(statement).first()

    if not ExtractedUser:
        raise HTTPException(status_code=404, detail="Usuario NO encontrado")
    
    if not verify_password(LoginUser.password,ExtractedUser.hashed_password):
        raise HTTPException(status_code=401, detail="Contraseña Incorrecta")
    
    else:
        return {"detail": "Ingreso Exitoso"}


@router.post("/recover")
def recuperar_contraseña(correo: str, session = Depends(get_session)):
    return
    