"""Generación del texto académico con la API de Anthropic (clave en Streamlit Secrets)."""
import json
import os
import re

import streamlit as st

MODELO_DEFECTO = "claude-sonnet-5-5"

SISTEMA = """Eres un asistente de redacción académica en español. Recibes un JSON con los datos de un ensayo,
las notas del autor por apartado y, opcionalmente, su lista de referencias.
Reglas estrictas:
1. Redacta cada apartado como texto académico formal, coherente y bien conectado con los demás, usando SOLO la información de las notas.
2. NO inventes fuentes, autores, obras, citas textuales, estadísticas, fechas ni datos. Si un apartado necesita evidencia que el autor no dio, escribe un marcador como [Agregar evidencia: ...] en lugar de inventarla.
3. Solo cita en el texto las fuentes presentes en la lista de referencias del autor, con el estilo de citación indicado y usando únicamente los datos que figuren en esa referencia.
4. No generes la lista de referencias.
5. Si un apartado ya tiene texto_actual, mejóralo respetando su contenido.
6. Incluye únicamente los apartados que recibas, con su mismo id.
7. Devuelve SOLO un objeto JSON válido {"id_del_apartado": "texto", ...}, sin Markdown ni comentarios. Separa párrafos con \\n."""

CITA = {"APA 7": "APA 7 (Autor, año)", "MLA": "MLA (Autor página)",
        "Chicago": "Chicago autor-fecha (Autor año)", "Formato libre": "criterio coherente y sencillo"}


def _secreto(nombre, defecto=None):
    try:
        return st.secrets[nombre]
    except Exception:
        return os.environ.get(nombre, defecto)


def disponible():
    return bool(_secreto("ANTHROPIC_API_KEY"))


def generar(e):
    import anthropic

    secs = [{"id": s["id"], "apartado": s["nombre"], "notas": s["notas"].strip(), "texto_actual": s["texto"].strip()}
            for s in e["secciones"] if not s["ref"] and (s["notas"].strip() or s["texto"].strip())]
    if not secs:
        raise ValueError("Escribe notas o texto en al menos un apartado (paso 3).")
    refs = [l.strip() for s in e["secciones"] if s["ref"] for l in s["texto"].split("\n") if l.strip()]
    carga = {"titulo": e["titulo"], "tipo_de_ensayo": e["tipo"], "asignatura": e["asignatura"],
             "estilo_de_citacion": CITA[e["formato"]], "referencias_del_autor": refs, "apartados": secs}
    cliente = anthropic.Anthropic(api_key=_secreto("ANTHROPIC_API_KEY"))
    r = cliente.messages.create(model=_secreto("ANTHROPIC_MODEL", MODELO_DEFECTO), max_tokens=8000, system=SISTEMA,
                                messages=[{"role": "user", "content": json.dumps(carga, ensure_ascii=False)}])
    txt = "".join(b.text for b in r.content if b.type == "text")
    m = re.search(r"\{.*\}", txt, re.S)
    if not m:
        raise ValueError("La respuesta de la IA no tuvo el formato esperado. Inténtalo de nuevo.")
    return {k: str(v) for k, v in json.loads(m.group(0)).items()}
