import requests
import os


if os.name == 'posix':  
        os.system('clear')
else: 
    os.system('cls')



# rta = requests.get(url)

# if rta.status_code == 200:
#     data = rta.json()
#     print(f'Nombre: {data[0][1]}')
#     print(f'Apellido: {data[0][2]}')
# else:
#     print("Ocurrio un error", rta.status_code)


opcion = True

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
         print(data)
    else:
         print("Ocurrio un error")

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
        opcion = True
        print("Elija una opcion")
        print(""" 
        1 => Ver mi perfil
        """)
        pregunta = input('>> ')
        # if pregunta == "1" or pregunta == "2" or pregunta == "3":
        #     opcion = False
        if pregunta == "1":
            date = data["access_token"]
            url = "http://127.0.0.1:8000/users/me"
            response = requests.get(url,data=date)
            if response.status_code == 200:
                data = response.json()
                print(data)
            else:
                print("Ocurrio un eror con su estado", response.status_code)
            

    else:
         print("Ocurrio un breve error")
         print(response.status_code)        











