import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.hash import bcrypt
from funciones import (
    conexion
)

db = conexion()
async def crear_usuario():

    username = "israel3"
    password = "Israel18"  
    role = "admin"
    print(repr(password))
    print(len(password.encode('utf-8')))



    hashed_password = bcrypt.hash(password)

 
    usuario_doc = {
        "username": username,
        "hashed_password": hashed_password,
        "role": role
    }

  
    result = await db["Usuarios"].insert_one(usuario_doc)
    print(f"Usuario creado con id: {result.inserted_id}")


asyncio.run(crear_usuario())
