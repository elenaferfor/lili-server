import requests
from .models import Libro, Autor, Editorial
from datetime import date
import re

# Archivo para usar Open Library como API externa
OPENLIBRARY_BASE_URL = "https://openlibrary.org"

def obtener_libro_por_isbn(isbn):
    edicion = _fetch_edicion(isbn)
    if not edicion:
        return None

    obra = _fetch_obra(edicion)
    return _mapear_libro(isbn, edicion, obra)

def _fetch_edicion(isbn):
    url = f"{OPENLIBRARY_BASE_URL}/isbn/{isbn}.json"
    response = requests.get(url, timeout=5)
    if response.status_code != 200:
        return None
    return response.json()


def _fetch_obra(edicion):
    works = edicion.get("works", [])
    if not works:
        return None
    obra_key = works[0].get("key")
    if not obra_key:
        return None

    url = f"{OPENLIBRARY_BASE_URL}{obra_key}.json"
    response = requests.get(url, timeout=5)
    if response.status_code != 200:
        return None
    return response.json()

def _mapear_libro(isbn, edicion, obra):
    return {
        "isbn": isbn,
        "titulo": edicion.get("title", ""),
        "sinopsis": _extraer_sinopsis(obra),
        "portada": _extraer_portada(edicion),
        "ano_pub": _extraer_fecha(edicion.get("publish_date")),
        "ano_pub_og": _extraer_fecha_og(obra),
        "openlibrary_key": _extraer_work_key(edicion),
        "formato": _mapear_formato(edicion.get("physical_format")),
        "editorial": _resolver_editorial(edicion),
        "autores": _resolver_autores(edicion),
    }


# FUNCIONES AUXILIARES PARA MAPEAR
def _extraer_sinopsis(obra):
    if not obra:
        return None
    descripcion = obra.get("description")
    if isinstance(descripcion, str):
        return descripcion
    if isinstance(descripcion, dict):
        return descripcion.get("value")
    return None

def _extraer_fecha(fecha_str):
    if not fecha_str:
        return None
    # Si la fecha está en formato ISO
    try:
        return date.fromisoformat(fecha_str)
    except ValueError:
        pass
    # Si sólo hay año
    match = re.search(r'\d{4}', fecha_str)
    if match:
        return date(int(match.group()), 1, 1)
    return None

def _extraer_fecha_og(obra):
    if not obra:
        return None
    return _extraer_fecha(obra.get("first_publish_date"))

def _resolver_autores(edicion):
    autores_data = edicion.get("authors", [])
    autores = []
    for entry in autores_data:
        autor_key = entry.get("key")
        if not autor_key:
            continue
        autor = Autor.objects.filter(openlibrary_key=autor_key.replace("/authors/", "")).first()
        if not autor:
            nombre = _fetch_nombre_autor(autor_key)
            if nombre:
                autor, _ = Autor.objects.get_or_create(
                    nombre=nombre,
                    defaults={"openlibrary_key": autor_key.replace("/authors/", "")}
                )
        if autor:
            autores.append(autor)
    return autores

def _fetch_nombre_autor(autor_key):
    url = f"{OPENLIBRARY_BASE_URL}{autor_key}.json"
    response = requests.get(url, timeout=5)
    if response.status_code != 200:
        return None
    return response.json().get("name")

def _resolver_editorial(edicion):
    editores = edicion.get("publishers", [])
    if not editores:
        return None
    nombre = editores[0]
    editorial, _ = Editorial.objects.get_or_create(nombre=nombre)
    return editorial

def _mapear_formato(formato_ol):
    if not formato_ol:
        return None
    formato_lower = formato_ol.lower()
    if "hardcover" in formato_lower or "tapa dura" in formato_lower:
        return Libro.FormatoLibro.TAPA_DURA
    if "paperback" in formato_lower or "tapa blanda" in formato_lower:
        return Libro.FormatoLibro.TAPA_BLANDA
    if "pocket" in formato_lower or "bolsillo" in formato_lower or "mass market" in formato_lower:
        return Libro.FormatoLibro.BOLSILLO
    return None

def _extraer_work_key(edicion):
    works = edicion.get("works", [])
    if not works:
        return None
    key = works[0].get("key", "")
    return key.replace("/works/", "") or None

def _extraer_portada(edicion):
    covers = edicion.get("covers", [])
    if not covers:
        return None
    return f"http://covers.openlibrary.org/b/id/{covers[0]}-L.jpg"