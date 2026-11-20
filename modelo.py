"""Datos, plantillas de apartados y estructura de cada formato académico."""
import datetime as dt
import uuid

TIPOS = {
    "Argumentativo": ["Introducción", "Contextualización", "Planteamiento del tema", "Tesis", "Argumentos",
                      "Evidencias y ejemplos", "Contraargumentos", "Conclusión", "Referencias bibliográficas"],
    "Expositivo": ["Introducción", "Contextualización", "Planteamiento del tema", "Desarrollo",
                   "Evidencias y ejemplos", "Conclusión", "Referencias bibliográficas"],
    "Crítico": ["Introducción", "Contextualización", "Tesis", "Desarrollo", "Argumentos",
                "Contraargumentos", "Conclusión", "Referencias bibliográficas"],
    "Reflexivo": ["Introducción", "Planteamiento del tema", "Desarrollo", "Evidencias y ejemplos",
                  "Conclusión", "Referencias bibliográficas"],
    "Comparativo": ["Introducción", "Contextualización", "Planteamiento del tema", "Tesis", "Desarrollo",
                    "Evidencias y ejemplos", "Conclusión", "Referencias bibliográficas"],
    "Analítico": ["Introducción", "Contextualización", "Planteamiento del tema", "Tesis", "Desarrollo",
                  "Evidencias y ejemplos", "Conclusión", "Referencias bibliográficas"],
    "Libre": ["Introducción", "Desarrollo", "Conclusión", "Referencias bibliográficas"],
}
DESCRIPCION = {
    "Argumentativo": "Defiende una tesis con argumentos, evidencias y refutación de posturas contrarias.",
    "Expositivo": "Explica un tema de forma clara, ordenada y objetiva.",
    "Crítico": "Evalúa una obra, idea o fenómeno con juicio fundamentado.",
    "Reflexivo": "Desarrolla una mirada personal y meditada sobre un tema.",
    "Comparativo": "Contrasta dos o más elementos para mostrar semejanzas y diferencias.",
    "Analítico": "Descompone un tema en partes para interpretarlo en profundidad.",
    "Libre": "Estructura mínima y flexible; tú decides los apartados.",
}
FORMATOS = ["APA 7", "MLA", "Chicago", "Formato libre"]
FORMATO_INFO = {
    "APA 7": "Portada, Times New Roman 12, interlineado doble, sangría de primera línea, número de página "
             "arriba a la derecha y «Referencias» con sangría francesa.",
    "MLA": "Sin portada: bloque con autor, docente, asignatura y fecha; título centrado, Times New Roman 12, "
           "interlineado doble, autor y página en el encabezado, sin títulos de apartado y «Obras citadas».",
    "Chicago": "Portada, Times New Roman 12, interlineado doble, página arriba a la derecha y «Bibliografía» "
               "con sangría francesa e interlineado sencillo.",
    "Formato libre": "Calibri 11, interlineado 1,15, texto justificado, número de página abajo y títulos a la izquierda.",
}
ESTILOS = {
    "APA 7": dict(fuente="Times New Roman", tam=12, inter=2.0, despues=0, sangria=True, just=False, centrar_h=True, pie=False),
    "MLA": dict(fuente="Times New Roman", tam=12, inter=2.0, despues=0, sangria=True, just=False, centrar_h=False, pie=False),
    "Chicago": dict(fuente="Times New Roman", tam=12, inter=2.0, despues=0, sangria=True, just=False, centrar_h=True, pie=False),
    "Formato libre": dict(fuente="Calibri", tam=11, inter=1.15, despues=8, sangria=False, just=True, centrar_h=False, pie=True),
}
NOMBRE_REF = {"APA 7": "Referencias", "MLA": "Obras citadas", "Chicago": "Bibliografía"}
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]


def fecha_larga(iso):
    try:
        d = dt.date.fromisoformat(iso)
        return f"{d.day} de {MESES[d.month - 1]} de {d.year}"
    except (ValueError, TypeError):
        return ""


def seccion(nombre):
    return {"id": uuid.uuid4().hex[:8], "nombre": nombre, "notas": "", "texto": "",
            "ref": nombre.strip().lower().startswith("referencias")}


def secciones_de(tipo):
    return [seccion(n) for n in TIPOS[tipo]]


def nuevo_ensayo(tipo="Argumentativo"):
    ahora = dt.datetime.now().isoformat(timespec="seconds")
    return {"id": uuid.uuid4().hex[:12], "titulo": "", "autor": "", "universidad": "", "carrera": "",
            "asignatura": "", "docente": "", "fecha": dt.date.today().isoformat(), "tipo": tipo,
            "formato": "APA 7", "titulos": True, "secciones": secciones_de(tipo),
            "creado": ahora, "actualizado": ahora}


def armar(e):
    """Devuelve la lista de bloques (tipo, texto) del documento según el formato.
    La usan tanto la vista previa como la exportación a Word."""
    f = e["formato"]
    B = []
    titulo = e.get("titulo", "").strip() or "Ensayo sin título"
    fecha = fecha_larga(e.get("fecha", ""))
    if f == "MLA":
        for x in (e.get("autor"), e.get("docente"), e.get("asignatura"), fecha):
            if x and x.strip():
                B.append(("left", x.strip()))
        B.append(("center", titulo))
    else:
        datos = [e.get(k, "").strip() for k in ("autor", "universidad", "carrera", "asignatura", "docente")] + [fecha]
        datos = [d for d in datos if d]
        portada = f in ("APA 7", "Chicago")
        if portada:
            B += [("vacio",)] * 3
        B.append(("title", titulo))
        B += [("center", d) for d in datos]
        if portada:
            B += [("pagebreak",), ("title", titulo)]
        else:
            B.append(("vacio",))
    for s in e["secciones"]:
        texto = s["texto"].strip()
        if not texto:
            continue
        if s["ref"]:
            lineas = [l.strip() for l in texto.split("\n") if l.strip()]
            if f != "Formato libre":
                lineas.sort(key=str.casefold)
                B.append(("pagebreak",))
            B.append(("h", NOMBRE_REF.get(f, s["nombre"])))
            B += [("ref", l) for l in lineas]
        else:
            if e.get("titulos", True) and f != "MLA":
                B.append(("h", s["nombre"]))
            B += [("p", l.strip()) for l in texto.split("\n") if l.strip()]
    return B
