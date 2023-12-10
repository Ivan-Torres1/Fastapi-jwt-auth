
from fastapi import FastAPI,Depends, HTTPException,status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt,JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from pymysql import Error
from envparse import Env
from typing import Type
from sqlmodel import SQLModel, create_engine,Session,Field,select 
from pydantic import EmailStr

# TERMINA DE HACER LOS EXECUTE A LA BASE DE DATOS, ARREGLA LA FUNCION VERIFYUSER Y MAS


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



url_db = f"mysql+pymysql://{useer}:{password}@{host}/{database}"
engine = create_engine(url=url_db,echo=True)





 #                                                                          SQL MODEL - MODELO DE TABLA
class User(SQLModel, table=True):
    id: Optional[int] = Field(
        default=None, 
        primary_key=True)
    
    name: str = Field(
        min_length=2,
        max_length=40,
        regex="^[A-Za-z]+$")
    
    lastname: str = Field(
        min_length=2, 
        max_length=40, 
        regex="^[A-Za-z]+$")
    
    password: str = Field(
        min_length=6, 
        regex="^(?=.*[A-Z])(?=.*[0-9]).*$")
    email: str = EmailStr
    

# ------------------------------------------------
class UserValidationEdit(SQLModel, table=True):
    id: Optional[int] = Field(
        default=None, 
        primary_key=True)

    name: Optional[str] = Field(
        min_length=2,
        max_length=40, 
        regex="^[A-Za-z]+$")

    lastname: Optional[str] = Field(
        min_length=2, 
        max_length=40, 
        regex="^[A-Za-z]+$")
    
    password: Optional[str] = Field(
        min_length=6, 
        regex="^(?=.*[A-Z])(?=.*[0-9]).*$")
    
    email: Optional[str] = EmailStr


# /////////////////////////////////////////////////////

#                                                                           FUNCIONES

def create_db():
     SQLModel.metadata.create_all(engine)


def Haspassword(password):
    hasheo = crypt.hash(password)
    return hasheo

def errordb(e):
    raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                    headers="OCURRIO UN ERROR CON LA BASE DE DATOS, INTENTE MAS TARDE",detail=e)

def VerifyUser(emailUser,nameUser):
    try:
        with Session(engine) as session:
            date = session.exec(select(User).where(User.email == emailUser, User.name == nameUser))
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al verificar usuario: {str(e)}")
    if date:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                        detail="Su gmail o nombre de usuario ya se ha usado para crear una cuenta",
                        headers={"ERROR":"NOT ACCEPTABLE"})
    






#                                   COMPRUEBA SI LA PERSONA SE LOGEO CORRECTAMENTE / COMPRUEBA EL TOKEN
async def comprobarToken(token: str = Depends(oauth2)):
    error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales de autenticación inválidas",
        headers={"WWW-Authenticate": "Bearer"})
    
    try:
        usernameDecode = jwt.decode(token,SECRET,algorithms=[ALGORITHM]).get("sub")
        if usernameDecode is None:
            raise error
    except JWTError:
        raise error
    
    try:
        with Session(engine) as session:
            username = session.exec(select(User.name,User.lastname,User.email,User.id).where(User.email == usernameDecode))
    except Error as e:
        errordb(e)

    return username
# ------------------------------------------------------------------------------------------------------




@app.get("/")
async def saludo():
    return {"Hola":"Mundo"}


#                                       VER TODOS LOS USUARIOS DE LA BASE DE DATOS
@app.get("/users")
async def users():
    try:
        with Session(engine) as session:
            users = session.exec(select(User)).all()
    except Error as e:
        errordb(e)
    return users                                




#                                        RETORNA INFORMACION DE USUARIO LOGEADO
@app.get("/users/me")
async def me(user: User = Depends(comprobarToken)):
    return user

# -------------------------------------------------------------------------------------------------------------------

#                                                REGISTER
@app.post("/users/registers")
async def registro(user: User):
    VerifyUser(user.email,user.name)
    contraseña = Haspassword(user.password)
    try:
        with Session(engine) as session:
            usuario = User(name=user.name,lastname=user.lastname,password=user.password,email=user.email)
            session.add(usuario)
            session.commit()
           
    except Exception as e:
                errordb(e)
    
    return {"message": "Se registro correctamente"}
# -------------------------------------------------------------------------------------------------------------------
#                                               LOGIN
@app.post("/users/login")
async def login(form: OAuth2PasswordRequestForm = Depends()):
    try:
        with Session(engine) as session:
            user = session.exec(select(User.email,User.password).where(User.email == form.username)).all()
    except Error as e:
        errordb(e)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    
    if not crypt.verify(form.password,user[1]): 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail="The password is incorrect")

    access_token = {"sub":user[0],
                   "exp": datetime.utcnow() + timedelta(minutes=ACCES_TOKEN_DURATION)}

    return {"access_token": jwt.encode(access_token,SECRET,algorithm=ALGORITHM),"token_type": "bearer"}
# -------------------------------------------------------------------------------------------------------------------


#                                               EDITA LA INFORMACION DE UN USUARIO
# EJEMPLO 
# http://127.0.0.1:8000/users/editUser/name?newdate=Aylen
@app.put("/users/editUser/{columnaName}")
async def editUsers(columnaName: str, newdate: str, user: User = Depends(comprobarToken)):
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
            with Session(engine) as session:
                date = session.exec(select(User.id).where(columnaName == newdate))
        except Error as e:
                errordb(e)
        if date:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="El correo ya esta en uso. Por favor, elija otro.")
 
    try:
        with Session(engine) as session:
            pass
            # cursor.execute(f"UPDATE users SET {columnaName} = %s WHERE id = %s", [newdate, user[3]])
            # db.commit()
    except Error as e:
                errordb(e)
    
    raise HTTPException(status_code=status.HTTP_200_OK,detail="Se actualizo correctamente el usuario")
    
    
    

#                                                   ELIMINAR UN USUARIO

@app.delete("/users/deleteuser/{emailUser}")
async def deleteUser(emailUser: str,user: User = Depends(comprobarToken),db: pymysql.connections.Connection = Depends(get_db)):
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE email = %s",[emailUser])
            dato = cursor.fetchone()
    except Error as e:
                errordb(e)
    if dato:
        if emailUser == user[2]:
            try:
                with db.cursor() as cursor:
                    cursor.execute("DELETE FROM users WHERE email = %s",[emailUser])
                    db.commit()
            except Error as e:
                errordb(e)
            raise HTTPException(status_code=status.HTTP_202_ACCEPTED,detail="Usuario eliminado correctamente")
            
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Debes iniciar sesion con el usuario para poder eliminarlo")
            
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="El usuario que desea eliminar no existe. Compruebe su informacion")



if __name__ == "__main__":
     create_db()
