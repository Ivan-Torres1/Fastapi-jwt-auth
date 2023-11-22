
from fastapi import FastAPI,Depends, HTTPException,status
from pydantic import BaseModel,EmailStr,Field
from re import Pattern
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt,JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import pymysql
from envparse import Env
from typing import Type
from sqlmodel import SQLModel




"""

{"name":"Marta",
"lastname":"Flores",
"password":"Familia123",
"email":"lamartamanda@gmail.com"}

# PatriManda123


"""


app = FastAPI()

env = Env()
env.read_envfile()



# CONECTION DATA BASE

host = env.str("host")
database = env.str("database")
useer = env.str("user")
password = env.str("password")

# VARIABLES
oauth2 = OAuth2PasswordBearer(tokenUrl="login")
ACCES_TOKEN_DURATION = 10
SECRET = env.str("SECRET")
ALGORITHM = "HS256"
crypt = CryptContext(schemes=["bcrypt"])




def get_db():
    db = pymysql.connect(host=host, port=3306, user=useer, db=database, passwd=password)
    try:
        yield db
    finally:
        db.close()
def get_db_dependency(db: pymysql.connections.Connection = Depends(get_db)):
    return db








#                                       Funciones 
def VerifyUser(email,name,db):
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE email=%s or name=%s",[email,name])
            date = cursor.fetchone()

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al verificar usuario: {str(e)}")
    if date:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                        detail="Su gmail o nombre de usuario ya se ha usado para crear una cuenta",
                        headers={"ERROR":"NOT ACCEPTABLE"})
    

def Haspassword(password):
    hasheo = crypt.hash(password)
    return hasheo



#                           COMPRUEBA SI LA PERSONA SE LOGEO CORRECTAMENTE / COMPRUEBA EL TOKEN
async def comprobarToken(token: str = Depends(oauth2),db: pymysql.connections.Connection = Depends(get_db)):
    error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales de autenticación inválidas",
        headers={"WWW-Authenticate": "Bearer"})
    
    try:
        username = jwt.decode(token,SECRET,algorithms=[ALGORITHM]).get("sub")
        if username is None:
            raise error
    except JWTError:
        raise error
    
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT name,lastname,email,id FROM users WHERE email=%s",[username])
            usernamee = cursor.fetchone()
    except pymysql.Error as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                    headers="OCURRIO UN ERROR CON LA BASE DE DATOS, INTENTE MAS TARDE",detail=e)

    return usernamee
# ------------------------------------------------------------------------------------------------------

#                           basemodel

class User(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=40,
        pattern="^[A-Za-z]+$")
    
    lastname: str = Field(
        min_length=2,
        max_length=40,
        pattern="^[A-Za-z]+$")

    password: str = Field( 
        min_length=7,
        pattern="^(?=.*[A-Z])(?=.*[0-9]).*$")
        
    
    def __get_pydantic_core_schema__(self, cls: Type["BaseModel"], **kwargs):
        return {
            "type": "string",
            "minLength": 7,
            "pattern": "^(?=.*[A-Z])(?=.*[0-9]).*$"}


    email: EmailStr


# ------------------------------------------------
class UserValidationEdit(BaseModel):
    name: Optional[Field(
        min_length=2,
        max_length=40,
        pattern="^[A-Za-z]+$")]
    
    lastname: Optional[Field(min_length=2,
        max_length=40,
        pattern="^[A-Za-z]+$")]

    password: Optional[Field( 
        min_length=7,
        pattern="^[A-Za-z]+$")]
    def __get_pydantic_core_schema__(self, cls: Type["BaseModel"], **kwargs):
        return {
            "type": "string",
            "minLength": 7,
            "pattern": "^(?=.*[A-Z])(?=.*[0-9]).*$"}
            
    email: Optional[EmailStr]




# /////////////////////////////////////////////////////


@app.get("/")
async def saludo():
    return {"Hola":"Mundo"}


#                                VER TODOS LOS USUARIOS DE LA BASE DE DATOS
@app.get("/users")
async def users(db: pymysql.connections.Connection = Depends(get_db)):
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()
    except pymysql.Error as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                    headers="OCURRIO UN ERROR CON LA BASE DE DATOS, INTENTE MAS TARDE",detail=e)
    # print(users, "ANANANANANANANANAN")
    return users                                




#                            RETORNA INFORMACION DE USUARIO LOGEADO
@app.get("/users/me")
async def me(user: User = Depends(comprobarToken)):
    print(user)
    return user


#                                     REGISTER
@app.post("/users/register")
async def registro(user: User,db: pymysql.connections.Connection = Depends(get_db) ):
    VerifyUser(user.email,user.name,db)
    contraseña = Haspassword(user.password)
    try:
        with db.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (name, lastname, email, password) VALUES (%s, %s, %s, %s)",
                (user.name, user.lastname, user.email, contraseña))
        db.commit()
    except pymysql.Error as e:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                    headers="OCURRIO UN ERROR CON LA BASE DE DATOS, INTENTE MAS TARDE",detail=e)
    
    return {"message": "Se registro correctamente"}
# -------------------------------------------------------------------------------------------------------------------
#                                    LOGIN
@app.post("/users/login")
async def login(form: OAuth2PasswordRequestForm = Depends(),db: pymysql.connections.Connection = Depends(get_db)):
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT email,password FROM users WHERE email=%s",[form.username])
            user = cursor.fetchone()
    except pymysql.Error as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                    headers="OCURRIO UN ERROR CON LA BASE DE DATOS, INTENTE MAS TARDE",detail=e)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    
    if not crypt.verify(form.password,user[1]): 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail="The password is incorrect")

    access_token = {"sub":user[0],
                   "exp": datetime.utcnow() + timedelta(minutes=ACCES_TOKEN_DURATION)}

    return {"access_token": jwt.encode(access_token,SECRET,algorithm=ALGORITHM),"token_type": "bearer"}
# -------------------------------------------------------------------------------------------------------------------


#                           EDITA LA INFORMACION DE UN USUARIO
# EJEMPLO 
# http://127.0.0.1:8000/users/editUser/name?newdate=Aylen
@app.put("/users/editUser/{columnaName}")
async def editUsers(columnaName: str, newdate: str, user: User = Depends(comprobarToken),db: pymysql.connections.Connection = Depends(get_db)):
    diccio = {columnaName: newdate}
    validation = UserValidationEdit(columnaName=newdate)
    try:
        validation.validate(value=diccio)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,headers="OCURRIO UN ERROR",detail=e)
        
    if columnaName == "password":
        newdate = Haspassword(newdate)
    elif columnaName == "email":
        try:
            with db.cursor() as cursor:
                cursor.execute(f"SELECT id FROM users WHERE {columnaName} = %s",[newdate])
                date = cursor.fetchone()
        except pymysql.Error as e:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                    headers="OCURRIO UN ERROR CON LA BASE DE DATOS, INTENTE MAS TARDE",detail=e)
        if date:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="El correo ya esta en uso. Por favor, elija otro.")
            
        else: 
            pass
 
    try:
        with db.cursor() as cursor:
            cursor.execute(f"UPDATE users SET {columnaName} = %s WHERE id = %s", [newdate, user[3]])
            db.commit()
    except pymysql.Error as e:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                    headers="OCURRIO UN ERROR CON LA BASE DE DATOS, INTENTE MAS TARDE",detail=e)
    
    raise HTTPException(status_code=status.HTTP_200_OK,detail="Se actualizo correctamente el usuario")
    
    
    

#                           ELIMINAR UN USUARIO

@app.delete("/users/deleteuser/{emailUser}")
async def deleteUser(emailUser: str,user: User = Depends(comprobarToken),db: pymysql.connections.Connection = Depends(get_db)):
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE email = %s",[emailUser])
            dato = cursor.fetchone()
    except pymysql.Error as e:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                    headers="OCURRIO UN ERROR CON LA BASE DE DATOS, INTENTE MAS TARDE",detail=e)
    if dato:
        if emailUser == user[2]:
            try:
                with db.cursor() as cursor:
                    cursor.execute("DELETE FROM users WHERE email = %s",[emailUser])
                    db.commit()
            except pymysql.Error as e:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                    headers="OCURRIO UN ERROR CON LA BASE DE DATOS, INTENTE MAS TARDE",detail=e)
            raise HTTPException(status_code=status.HTTP_202_ACCEPTED,detail="Usuario eliminado correctamente")
            
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Debes iniciar sesion con el usuario para poder eliminarlo")
            
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="El usuario que desea eliminar no existe. Compruebe su informacion")




