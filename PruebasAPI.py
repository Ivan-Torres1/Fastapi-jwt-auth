import requests
import os
from tabulate import tabulate



# LIMPIAR LA CONSOLA
# if os.name == 'posix':  
#         os.system('clear')
# else: 
#     os.system('cls')



opcion = True

# OPCIONES
print("Bienvenido a tu web")
print("Elija una opcion")
while opcion:

    print(""" 
        1 => Registrarse
        2 => Iniciar sesion
        3 => Ver todos los usuarios  

        """)
    
    pregunta = input('>> ')
    
    if pregunta == "1" or pregunta == "2" or pregunta == "3":
          opcion = False
    else:
          print("Esa opcion no existe. Vuelve a intentarlo")

#           REGISTRAR UN USUARIO
if pregunta == "1":
    print("Nombre")
    nombre = input('>> ')
    print("Apellido")
    apellido = input('>> ')
    print('Contraseña')
    password = input('>> ')
    print('Email')
    email = input('>> ')

    sendDate = {
         "name": nombre,
         "lastname": apellido,
         "password": password,
         "email": email}

    url = "http://127.0.0.1:8000/register"
    response = requests.post(url,json=sendDate)
    if response.status_code == 200:
         data = response.json()
         print("Se registro correctamente")
    else:
         print("Ocurrio un error")

#  INICIO DE SESION DE UN USUARIO YA CREADO EN LA BASE DE DATOS
if pregunta == "2":
    print("Email")
    email = input(">> ")
    print("Contraseña")
    password = input(">> ")

    sendDate = {"username" : email,
                "password":password}

    url = "http://127.0.0.1:8000/login"
    response = requests.post(url,data=sendDate)
    if response.status_code == 200:
        data = response.json()
        print("Inicio sesión correctamente")
        print("Elija una opcion")
        miopcion = True
        while miopcion: 
            print("1 => Ver mi perfil")

            pregunta = input('>> ')
    
            if pregunta == "1":
                miopcion = False
        if miopcion == False:
            date = data["access_token"]
            url = "http://127.0.0.1:8000/users/me"
            headers = {"Authorization": f"Bearer {date}"}

            response = requests.get(url,headers=headers)
            if response.status_code == 200:
                data = response.json()
                dataLista = [data]
                head = ["NOMBRE","APELLIDO","EMAIL"]
                tablePerfil = tabulate(dataLista,headers=head,tablefmt="simple")
                print(tablePerfil)
                print()

            else:
                print("Ocurrio un eror con su estado", response.status_code)
    else:
        print(f"Ocurrio un error {response.status_code} {response.text}")

        
if pregunta == "3":
    url = "http://127.0.0.1:8000/users"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        headers = ["ID","NOMBRE","APELLIDO","CONTRASEÑA","EMAIL"]
        table = tabulate(data,headers=headers,tablefmt="orgtbl",stralign="center",rowsep=2)
        print(table)
        print()




             
      











