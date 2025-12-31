from conexion import obtener_conexion
from fastapi import HTTPException, Header
from modelos import TagUpdate

db = obtener_conexion()

def conexion():
    return db

def fix_mongo_id(doc):
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc

async def verificar_token(x_token: str = Header(...)):
    usuario = await db["Usuarios"].find_one({"token": x_token})
    if not usuario:
        raise HTTPException(status_code=401, detail="Token inválido")
    return usuario

# ---------------- GET JUEGO ----------------
async def obtener_juego_nombre(name: str, page: int = 1, page_size: int = 2):
    skip = (page - 1) * page_size

    total = await db["Juegos"].count_documents(
        {"name": {"$regex": name, "$options": "i"}}
    )

    cursor = (
        db["Juegos"]
        .find({"name": {"$regex": name, "$options": "i"}})
        .skip(skip)
        .limit(page_size)
    )

    results = [doc["name"] async for doc in cursor]

    return {
        "page": page,
        "page_size": page_size,
        "total": total,      
        "results": results
    }


# ---------------- POST GENERO ----------------
async def crear_genero(id: int, name: str, slug: str):
    existe = await db["Generos"].find_one({"id": id})
    if existe:
        raise HTTPException(status_code=400, detail="El género ya existe")

    genero = {"id": id, "name": name, "slug": slug.lower(), "games_count":0, "image_background":""}
    await db["Generos"].insert_one(genero)

    return {"message": "Género creado", "genero": fix_mongo_id(genero)}


# ---------------- DELETE DESARROLLADOR ----------------
async def eliminar_desarrollador(dev_id: int):
    result = await db["Desarrolladores"].delete_one({"id": dev_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Desarrollador no encontrado")

    return {"message": "Desarrollador eliminado correctamente"}


# ---------------- PUT TAG ----------------
async def actualizar_tag(tag_id: int, data: TagUpdate):
    update_fields = {}

    if data.name is not None:
        update_fields["name"] = data.name

    if data.slug is not None:
        update_fields["slug"] = data.slug.lower() 

    if data.games_count is not None:
        update_fields["games_count"] = data.games_count

    if data.image_background is not None:
        update_fields["image_background"] = data.image_background

    if data.score is not None:
        update_fields["score"] = data.score

    if not update_fields:
        raise HTTPException(status_code=400, detail="No hay campos para actualizar")

    result = await db["Tags"].update_one(
        {"id": tag_id},
        {"$set": update_fields}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Tag no encontrado")

    return {
        "message": "Tag actualizado",
        "id": tag_id,
        "updated_fields": update_fields
    }

