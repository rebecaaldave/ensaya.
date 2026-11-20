"""Persistencia sencilla en archivos JSON (uno por código personal)."""
import datetime as dt
import hashlib
import json
from pathlib import Path

DIR = Path(__file__).parent / "data"


def _ruta(codigo):
    h = hashlib.sha256(codigo.strip().lower().encode("utf-8")).hexdigest()[:24]
    return DIR / f"{h}.json"


def listar(codigo):
    r = _ruta(codigo)
    if not r.exists():
        return []
    try:
        datos = json.loads(r.read_text("utf-8"))
    except (ValueError, OSError):
        return []
    return sorted(datos, key=lambda x: x.get("actualizado", ""), reverse=True)


def _escribir(codigo, lista):
    DIR.mkdir(exist_ok=True)
    r = _ruta(codigo)
    tmp = r.with_suffix(".tmp")
    tmp.write_text(json.dumps(lista, ensure_ascii=False, indent=1), "utf-8")
    tmp.replace(r)


def guardar(codigo, ensayo):
    ensayo["actualizado"] = dt.datetime.now().isoformat(timespec="seconds")
    lista = [x for x in listar(codigo) if x["id"] != ensayo["id"]]
    lista.append(ensayo)
    _escribir(codigo, lista)


def eliminar(codigo, ensayo_id):
    _escribir(codigo, [x for x in listar(codigo) if x["id"] != ensayo_id])
