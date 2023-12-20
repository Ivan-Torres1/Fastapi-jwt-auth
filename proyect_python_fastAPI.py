
from fastapi import FastAPI,Depends, HTTPException,status
from pydantic import ValidationError
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt,JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.exc import SQLAlchemyError
from envparse import Env
from typing import Type
from sqlmodel import SQLModel, create_engine,Session,Field,select,or_
from pydantic import EmailStr
import pymysql



"""

{"name":"Marta",
"lastname":"Flores",
"password":"Familia123",
"email":"lamartamanda@gmail.com"}

# PatriManda123


"""


app = FastAPI()

pathEnv = "config/.env"
env = Env()
env.read_envfile(pathEnv)



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
engine = create_engine(url=url_db)




 #                                                                          SQL MODEL - MODELO DE TABLA

# ------------------------------------------------
class User(SQLModel, table=True):
    __tablename__ = "users"
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
    
    email: Optional[EmailStr] = Field(index=True)

  


# /////////////////////////////////////////////////////

#                                                                           FUNCIONES

def create_db():
     SQLModel.metadata.create_all(engine)


def Haspassword(password):
    hasheo = crypt.hash(password)
    return hasheo

def errordb(e):
    raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                    detail=f"OCURRIO UN ERROR CON LA BASE DE DATOS, INTENTE MAS TARDE {e}")

def VerifyUser(emailUser,nameUser):
    try:
        with Session(engine) as session:
            date = session.exec(select(User.name).where(or_(User.email == emailUser,User.name == nameUser))).first()
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al verificar usuario: {str(e)}")
    
    if date:

        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                        detail="Su gmail o nombre de usuario ya estan en uso. Por favor, pruebe con otro.",
                        headers={"ERROR":"NOT ACCEPTABLE"})
    
# En la funcion "VerifyUser" hay formas de hacerlo mejor pero, como en mi caso queria probar y aprender a como usar los indices para 
# hacer consultas mas eficientes, no encuentro mejor forma de hacerlo que no sea asi. Podria agregar mas indices pero no se si seria mas
# eficientes en cuanto a recursos que usaria y el tamaño. En fin, solo lo hago de prueba, en otro caso esperaria a ver los recursos que tengo
# y accionar luego, este es un caso hipotetico.





 

#                                   COMPRUEBA SI LA PERSONA SE LOGEO CORRECTAMENTE / COMPRUEBA EL TOKEN
async def comprobarToken(token: str = Depends(oauth2)):
    error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales de autenticación inválidas",
        headers={"WWW-Authenticate": "Bearer"})

    try:
        usernameDecode = jwt.decode(token,SECRET,algorithms=[ALGORITHM]).get("sub")    
        
    except JWTError:
        raise error

    if usernameDecode is None:
        raise error

    try:
        
        with Session(engine) as session:
            username = session.exec(select(User.name,User.lastname,User.email,User.id).where(usernameDecode == User.email)).all()
    except SQLAlchemyError as e:
        errordb(e)
    us_tupla = username[0]
    us_tupla = tuple(us_tupla)
    return us_tupla
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

    except SQLAlchemyError as e:
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
            usuario = User(name=user.name,lastname=user.lastname,password=contraseña,email=user.email)
            session.add(usuario)
            session.commit()
           
    except SQLAlchemyError as e:
                errordb(e)
    
    return {"message": f"Se registro correctamente"}
# -------------------------------------------------------------------------------------------------------------------
#                                               LOGIN
@app.post("/users/login")
async def login(form: OAuth2PasswordRequestForm = Depends()):
    print("HOLA MUNDOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
    try:
        with Session(engine) as session:
            user = session.exec(select(User.email,User.password).where(form.username == User.email)).first()

    except SQLAlchemyError as e:
        errordb(e)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not founnd")
    
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
@app.put("/users/editUser/{column_extracted}")
async def editUsers(column_extracted: str, newdate: str, user: User = Depends(comprobarToken)):
   
    diccio = {column_extracted: newdate}
    usuario = User()
    try:
        usuario.validate(value=diccio)
    except ValueError as e: 
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                            detail=f"ERROR DE VALIDACIÓN {e}")
 
    if column_extracted == "password":
        newdate = Haspassword(newdate)

    elif column_extracted == "email":
        atributo = getattr(User,column_extracted)
        try:
            with Session(engine) as session:
                date = session.exec(select(User.id).where(atributo == newdate)).first()
                
        except SQLAlchemyError as e:
                errordb(e)
        if date:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="El correo ya esta en uso. Por favor, elija otro.")

    gmailUser = user[2]
  
    try:
        with Session(engine) as session:
            userUpdate = session.exec(select(User).where(gmailUser == User.email)).first()
              
            setattr(userUpdate, column_extracted,newdate)
            session.commit()
            session.refresh(userUpdate)
    except SQLAlchemyError as e:
                errordb(e)
  

    raise HTTPException(status_code=status.HTTP_200_OK,detail="Se actualizo correctamente el usuario")

    
    
    

#                                                         ELIMINAR UN USUARIO

@app.delete("/users/deleteuser/{emailUser}")
async def deleteUser(emailUser: str,user: User = Depends(comprobarToken)):
    try:
        with Session(engine) as session:
            dato = session.exec(select(User.id).where(emailUser == User.email)).first()
            print(dato)
    except SQLAlchemyError as e:
                errordb(e)
    if dato:
        if emailUser == user[2]:
            try:
                with Session(engine) as session:
                    userr = session.exec(select(User).where(emailUser == User.email)).first()
                    session.delete(userr)
                    session.commit()
            except SQLAlchemyError as e:
                errordb(e)
            raise HTTPException(status_code=status.HTTP_202_ACCEPTED,detail="Usuario eliminado correctamente")
            
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Debes iniciar sesion con el usuario para poder eliminarlo")
            
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="El usuario que desea eliminar no existe. Compruebe su informacion")



if __name__ == "__main__":
     create_db()
