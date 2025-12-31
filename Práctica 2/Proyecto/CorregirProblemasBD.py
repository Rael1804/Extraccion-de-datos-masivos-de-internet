from pymongo import MongoClient
import json
import ast
import re

# Conectar a MongoDB con autenticación
client = MongoClient("mongodb://localhost:27017/")
db = client["EDMI"]

Desarrolladores_collection= db["Desarrolladores"]
Generos_collection= db["Generos"]
Juegos_collection= db["Juegos"]
Tags_collection= db["Tags"]

def reemplazar_nulls(doc):
    """
    Recorre un diccionario (documento) y reemplaza todos los None por "".
    Funciona recursivamente para diccionarios anidados y listas.
    """
    if isinstance(doc, dict):
        return {k: reemplazar_nulls(v) for k, v in doc.items()}
    elif isinstance(doc, list):
        return [reemplazar_nulls(item) for item in doc]
    elif doc is None:
        return ""
    else:
        return doc

def preprocesar_dev(dev, original_id):
    """Normaliza un documento de results"""
    return {
        "_original_id": original_id,
        "id": dev.get("id"),
        "name": dev.get("name") or "",
        "slug": dev.get("slug") or "",
        "games_count": dev.get("games_count", 0),
        "top_games": dev.get("top_games", []),
        "image_background": dev.get("image_background") or "",
        "score": float(dev["score"]) if dev.get("score") else 0.0,
        "text": dev.get("text") or ""
    }

def preprocesar_gen(gen, original_id):
    """Normaliza un documento de results"""
    return {
        "_original_id": original_id,
        "id": gen.get("id"),
        "name": gen.get("name") or "",
        "slug": gen.get("slug") or "",
        "games_count": gen.get("games_count", 0),
        "image_background": gen.get("image_background") or "",
    }

def preprocesar_tag(tag, original_id):
    """Normaliza un documento de results"""
    return {
        "_original_id": original_id,
        "id": tag.get("id"),
        "name": tag.get("name") or "",
        "slug": tag.get("slug") or "",
        "games_count": tag.get("games_count", 0),
        "image_background": tag.get("image_background") or "",
        "score": float(tag["score"]) if tag.get("score") else 0.0,
    }

def arreglar_desarrolladores():
    docs = list(Desarrolladores_collection.find({}))
    documentos_nuevos=[]

    for doc in docs:
          original_id= doc.get("_id")
          results = doc.get("results", [])
          for r in results:
                documentos_nuevos.append(preprocesar_dev(r, original_id))
    
    if documentos_nuevos:
          Desarrolladores_collection.insert_many(documentos_nuevos)

          Desarrolladores_collection.delete_many({"results": {"$exists": True}})

def arreglar_generos():
    docs = list(Generos_collection.find({}))
    documentos_nuevos=[]

    for doc in docs:
          original_id= doc.get("_id")
          results = doc.get("results", [])
          for r in results:
                documentos_nuevos.append(preprocesar_gen(r, original_id))
    
    if documentos_nuevos:
          Generos_collection.insert_many(documentos_nuevos)

          Generos_collection.delete_many({"results": {"$exists": True}})

def arreglar_tags():
    docs = list(Tags_collection.find({}))
    documentos_nuevos=[]

    for doc in docs:
          original_id= doc.get("_id")
          results = doc.get("results", [])
          for r in results:
                documentos_nuevos.append(preprocesar_tag(r, original_id))
    
    if documentos_nuevos:
          Tags_collection.insert_many(documentos_nuevos)

          Tags_collection.delete_many({"results": {"$exists": True}})

def arreglar_juegos():
    for doc in Juegos_collection.find({}):
        doc_id = doc["_id"]
        doc_limpio = reemplazar_nulls(doc)
        Juegos_collection.replace_one({"_id": doc_id}, doc_limpio)
# # Ejecutar normalizaciones
if __name__ == "__main__":
        arreglar_desarrolladores()
        arreglar_generos()
        arreglar_tags()
        arreglar_juegos()

