from fastapi import FastAPI, HTTPException, Request, Depends, Body, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import time
from passlib.hash import bcrypt
import secrets

from funciones import (
    obtener_juego_nombre,
    eliminar_desarrollador,
    actualizar_tag,
    crear_genero,
    verificar_token,
    conexion
)
from modelos import GenreCreate, TagUpdate

db = conexion()

rate_limit_data = {}

MAX_REQUESTS = 10  
WINDOW_SECONDS = 100  


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def rate_limiter(request: Request):
    ip = request.client.host
    now = time.time()

    if ip not in rate_limit_data:
        rate_limit_data[ip] = {"inicio": now, "count": 1}
        return

    info = rate_limit_data[ip]

    if now - info["inicio"] < WINDOW_SECONDS:
        if info["count"] >= MAX_REQUESTS:
            raise HTTPException(
                status_code=429,
                detail="Demasiadas peticiones. Intenta de nuevo más tarde."
            )
        info["count"] += 1
    else:
        rate_limit_data[ip] = {"inicio": now, "count": 1}


# ---------------- Auth ----------------


@app.post("/login")
async def login(username: str = Body(...), password: str = Body(...)):
    usuario = await db["Usuarios"].find_one({"username": username})
    if not usuario or not bcrypt.verify(password, usuario["hashed_password"]):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    
    token = secrets.token_hex(16)
    await db["Usuarios"].update_one({"username": username}, {"$set": {"token": token}})
    return {"token": token}


@app.get("/")
def read_root():
    return {"message": "Bienvenido a la práctica 2"}

# ---------------- GET JUEGO ----------------
@app.get("/juego/nombre/{nombre}")
async def get_juego(
    nombre: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    _ = Depends(rate_limiter)
):
    try:
        return await obtener_juego_nombre(nombre, page, page_size)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------- DELETE DESARROLLADOR ----------------
@app.delete("/desarrollador/{desarrollador_id}")
async def eliminar_desarrollador_endpoint(
    desarrollador_id: int,
    _ = Depends(rate_limiter),
    usuario = Depends(verificar_token)
):
    try:
        return await eliminar_desarrollador(desarrollador_id)
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Error eliminando desarrollador")


# ---------------- PUT TAG ----------------
@app.put("/tag/{tag_id}")
async def actualizar_tag_endpoint(
    tag_id: int,
    data: TagUpdate,
    _ = Depends(rate_limiter),
    usuario = Depends(verificar_token)
):
    try:
        return await actualizar_tag(tag_id, data)
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Error actualizando tag")


# ---------------- POST GENERO ----------------
@app.post("/genero")
async def crear_genero_endpoint(
    genero: GenreCreate,
    _ = Depends(rate_limiter),
    usuario = Depends(verificar_token)
):
    try:
        return await crear_genero(genero.id, genero.name, genero.slug)
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Error creando género")


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    key_path = os.path.join(current_dir, "..", "certs", "key.pem")
    cert_path = os.path.join(current_dir, "..", "certs", "cert.pem")

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        ssl_keyfile=key_path,
        ssl_certfile=cert_path,
        reload=True
    )