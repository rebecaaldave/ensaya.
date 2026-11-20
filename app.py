"""ENSAYA: generador de ensayos académicos. Ejecutar con: streamlit run app.py"""
import datetime as dt
import html
import json
import re

import streamlit as st

import almacen
import ia
import modelo
from exportar import construir_docx

st.set_page_config(page_title="ENSAYA", page_icon="📝", layout="wide")
st.markdown("""<style>
.block-container{max-width:1100px;padding-top:2rem}
.hero{background:linear-gradient(135deg,#EAF1FB,#FFFFFF);border:1px solid #D9E2F0;border-radius:18px;
 padding:3rem 1.5rem;text-align:center;margin-bottom:1.5rem}
.hero h1{font-size:3.2rem;letter-spacing:.2em;color:#1F5FBF;margin:0}
.hero p{color:#4B5563;font-size:1.1rem;max-width:640px;margin:1rem auto 0}
.tarjeta{border:1px solid #E5E7EB;border-radius:14px;padding:1.1rem 1.2rem;background:#fff;height:100%}
.tarjeta h4{color:#1F5FBF;margin:0 0 .4rem}.tarjeta p{color:#4B5563;margin:0}
.hoja{background:#fff;border:1px solid #CBD5E1;box-shadow:0 4px 18px rgba(31,41,55,.08);
 padding:2.5rem 3rem;color:#111;border-radius:4px}
.hoja p{margin:0}
@media(max-width:700px){.hero h1{font-size:2.2rem}.hoja{padding:1.2rem}}
</style>""", unsafe_allow_html=True)

S = st.session_state
PAGINAS = ["Inicio", "Editor", "Mis trabajos"]
PASOS = ["1. Datos generales", "2. Tipo y formato", "3. Apartados", "4. Redacción", "5. Vista previa y descarga"]
S.setdefault("pagina_v", "Inicio")
S.setdefault("paso_v", PASOS[0])
S.setdefault("ensayo", None)


def ir(pagina, paso=None):
    S.pagina_v = pagina
    if paso:
        S.paso_v = paso


def nuevo():
    S.ensayo = modelo.nuevo_ensayo()
    ir("Editor", PASOS[0])


def abrir(ensayo):
    S.ensayo = ensayo
    ir("Editor", PASOS[0])


def entrada(obj, campo, etiqueta, tipo="texto", **kw):
    """Widget enlazado a obj[campo]; la clave incluye el id del ensayo para no mezclar estados."""
    k = f"{campo}_{S.ensayo['id']}_{obj['id']}"
    if k not in S:
        S[k] = dt.date.fromisoformat(obj[campo]) if tipo == "fecha" else obj[campo]
    if tipo == "area":
        v = st.text_area(etiqueta, key=k, **kw)
    elif tipo == "fecha":
        v = st.date_input(etiqueta, key=k, format="DD/MM/YYYY").isoformat()
    elif tipo == "check":
        v = st.checkbox(etiqueta, key=k, **kw)
    else:
        v = st.text_input(etiqueta, key=k, **kw)
    obj[campo] = v


# ---------------------------------------------------------------- Inicio
def inicio():
    st.markdown('<div class="hero"><h1>ENSAYA</h1><p>Organiza tus ideas, redacta con apoyo de inteligencia '
                'artificial y descarga tu ensayo en Word con el formato académico que necesitas.</p></div>',
                unsafe_allow_html=True)
    _, c, _ = st.columns([1, 1, 1])
    c.button("Crear nuevo ensayo", type="primary", use_container_width=True, on_click=nuevo)
    st.write("")
    datos = [("Estructura guiada", "Apartados adaptados a cada tipo de ensayo; puedes agregar o quitar los que quieras."),
             ("Formatos académicos", "APA 7, MLA, Chicago o formato libre, aplicados al documento Word."),
             ("Tus trabajos guardados", "Guarda, retoma, edita y elimina tus ensayos cuando quieras.")]
    for col, (t, d) in zip(st.columns(3), datos):
        col.markdown(f'<div class="tarjeta"><h4>{t}</h4><p>{d}</p></div>', unsafe_allow_html=True)


# ---------------------------------------------------------------- Editor
def p_datos(e):
    a, b = st.columns(2)
    with a:
        entrada(e, "titulo", "Título del ensayo")
        entrada(e, "autor", "Autor")
        entrada(e, "universidad", "Universidad")
        entrada(e, "carrera", "Carrera o escuela")
    with b:
        entrada(e, "asignatura", "Asignatura")
        entrada(e, "docente", "Docente")
        entrada(e, "fecha", "Fecha", tipo="fecha")


def p_tipo(e):
    a, b = st.columns(2)
    with a:
        tipos = list(modelo.TIPOS)
        tipo = st.selectbox("Tipo de ensayo", tipos, index=tipos.index(e["tipo"]))
        st.caption(modelo.DESCRIPCION[tipo])
        hay = any(s["notas"].strip() or s["texto"].strip() for s in e["secciones"])
        if tipo != e["tipo"]:
            e["tipo"] = tipo
            if not hay:
                e["secciones"] = modelo.secciones_de(tipo)
                st.rerun()
        if st.button("Restablecer apartados según el tipo"):
            e["secciones"] = modelo.secciones_de(tipo)
            st.rerun()
        if hay:
            st.caption("Ya hay contenido escrito: los apartados solo cambian si pulsas el botón (se perderá lo escrito).")
    with b:
        f = st.selectbox("Formato académico", modelo.FORMATOS, index=modelo.FORMATOS.index(e["formato"]))
        e["formato"] = f
        st.caption(modelo.FORMATO_INFO[f])
        entrada(e, "titulos", "Mostrar títulos de apartados (MLA no los usa)", tipo="check")


def p_apartados(e):
    st.caption("Escribe notas, ideas y datos de cada apartado: la IA los convertirá en texto sin añadir información "
               "que no hayas dado. En referencias, escribe una por línea ya con su formato.")
    for s in list(e["secciones"]):
        with st.container(border=True):
            a, b = st.columns([6, 1])
            a.markdown(f"**{s['nombre']}**")
            if b.button("Quitar", key=f"del_{e['id']}_{s['id']}"):
                e["secciones"].remove(s)
                st.rerun()
            if s["ref"]:
                entrada(s, "texto", "Referencias (una por línea)", tipo="area", height=140)
            else:
                entrada(s, "notas", "Notas e ideas", tipo="area", height=120)
    with st.form(f"nuevo_{e['id']}", clear_on_submit=True):
        nombre = st.text_input("Nombre de un apartado nuevo")
        ok = st.form_submit_button("Agregar apartado")
    if ok and nombre.strip():
        i = next((i for i, s in enumerate(e["secciones"]) if s["ref"]), len(e["secciones"]))
        e["secciones"].insert(i, modelo.seccion(nombre.strip()))
        st.rerun()


def campos_texto(e):
    for s in e["secciones"]:
        entrada(s, "texto", s["nombre"], tipo="area", height=140 if s["ref"] else 220)


def p_redaccion(e):
    st.caption("Genera el texto a partir de tus notas y luego edítalo libremente. También puedes escribir "
               "directamente en cada apartado sin usar IA.")
    activo = ia.disponible()
    if not activo:
        st.warning("La IA no está configurada: agrega ANTHROPIC_API_KEY en Streamlit Secrets (ver README). "
                   "Mientras tanto puedes redactar manualmente.")
    if st.button("Organizar y generar ensayo con IA", type="primary", disabled=not activo):
        try:
            with st.spinner("Redactando tu ensayo..."):
                res = ia.generar(e)
            for s in e["secciones"]:
                if s["id"] in res and not s["ref"]:
                    s["texto"] = res[s["id"]]
                    S[f"texto_{e['id']}_{s['id']}"] = res[s["id"]]
            st.success("Texto generado. Revisa cada apartado, verifica los datos y edítalo antes de descargar.")
        except Exception as ex:
            st.error(f"No se pudo generar el texto: {ex}")
    campos_texto(e)


def vista_html(e):
    f = e["formato"]
    c = modelo.ESTILOS[f]
    sangria = "text-indent:1.27cm;" if c["sangria"] else ""
    just = "text-align:justify;" if c["just"] else ""
    out = []
    for b in modelo.armar(e):
        k = b[0]
        t = html.escape(b[1]) if len(b) > 1 else ""
        if k == "title":
            out.append(f"<p style='text-align:center;font-weight:bold'>{t}</p>")
        elif k == "center":
            out.append(f"<p style='text-align:center'>{t}</p>")
        elif k == "left":
            out.append(f"<p>{t}</p>")
        elif k == "vacio":
            out.append("<p>&nbsp;</p>")
        elif k == "pagebreak":
            out.append("<hr style='margin:2rem 0;border-top:2px dashed #CBD5E1'>")
        elif k == "h":
            al = "center" if c["centrar_h"] else "left"
            out.append(f"<p style='text-align:{al};font-weight:bold'>{t}</p>")
        elif k == "p":
            out.append(f"<p style='{sangria}{just}'>{t}</p>")
        elif k == "ref":
            out.append(f"<p style='padding-left:1.27cm;text-indent:-1.27cm'>{t}</p>")
    fuente = f"font-family:{c['fuente']},serif;font-size:{c['tam'] + 3}px;line-height:{c['inter']};"
    return f"<div class='hoja' style=\"{fuente}\">{''.join(out)}</div>"


def p_vista(e):
    barra = st.container()
    editar = st.toggle("Editar el contenido aquí", key=f"ed_{e['id']}")
    if editar:
        izq, der = st.columns(2)
        with izq:
            campos_texto(e)
        with der:
            st.markdown(vista_html(e), unsafe_allow_html=True)
    else:
        st.markdown(vista_html(e), unsafe_allow_html=True)
    hay = any(s["texto"].strip() for s in e["secciones"])
    nombre = re.sub(r"[^\w\-]+", "_", e["titulo"].strip())[:60].strip("_") or "ensayo"
    with barra:
        st.download_button("Descargar Word (.docx)", data=construir_docx(e), file_name=f"{nombre}.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                           type="primary", disabled=not hay)
        if not hay:
            st.info("Aún no hay texto. Redáctalo en el paso 4 o activa la edición aquí.")


def guardar_actual():
    cod = S.get("codigo", "").strip()
    if not cod:
        st.warning("Escribe tu código personal en la barra lateral para guardar.")
        return
    almacen.guardar(cod, S.ensayo)
    st.toast("Ensayo guardado en Mis trabajos.")


def editor():
    e = S.ensayo
    if e is None:
        st.info("No hay un ensayo abierto.")
        st.button("Crear nuevo ensayo", type="primary", on_click=nuevo)
        return
    a, b = st.columns([5, 1])
    paso = a.radio("Paso", PASOS, index=PASOS.index(S.paso_v), horizontal=True, label_visibility="collapsed")
    S.paso_v = paso
    guardar = b.button("Guardar", use_container_width=True)
    st.divider()
    {PASOS[0]: p_datos, PASOS[1]: p_tipo, PASOS[2]: p_apartados, PASOS[3]: p_redaccion, PASOS[4]: p_vista}[paso](e)
    if guardar:  # después de los widgets, para guardar los valores más recientes
        guardar_actual()


# ---------------------------------------------------------------- Mis trabajos
def trabajos():
    st.markdown("### Mis trabajos")
    cod = S.get("codigo", "").strip()
    if not cod:
        st.info("Escribe tu código personal en la barra lateral para ver tus ensayos guardados.")
        return
    lista = almacen.listar(cod)
    if not lista:
        st.info("Aún no tienes ensayos guardados con este código.")
    for e in lista:
        with st.container(border=True):
            a, b, c = st.columns([5, 1.4, 1.2])
            a.markdown(f"**{e.get('titulo') or 'Sin título'}**  \n{e['tipo']} · {e['formato']} · "
                       f"modificado {e['actualizado'][:16].replace('T', ' ')}")
            b.button("Abrir y editar", key=f"ab_{e['id']}", on_click=abrir, args=(e,), use_container_width=True)
            with c.popover("Eliminar", use_container_width=True):
                st.write("Esta acción no se puede deshacer.")
                if st.button("Confirmar eliminación", key=f"el_{e['id']}"):
                    almacen.eliminar(cod, e["id"])
                    if S.ensayo and S.ensayo["id"] == e["id"]:
                        S.ensayo = None
                    st.rerun()
    st.button("Crear nuevo ensayo", on_click=nuevo)
    st.divider()
    st.markdown("**Copia de seguridad**")
    st.caption("El almacenamiento de Streamlit Community Cloud puede borrarse al reiniciar la app. "
               "Descarga una copia y restáurala cuando la necesites.")
    st.download_button("Descargar copia (.json)", json.dumps(lista, ensure_ascii=False, indent=1),
                       "ensaya_copia.json", "application/json", disabled=not lista)
    arch = st.file_uploader("Restaurar copia", type="json")
    if arch is not None and st.button("Importar ensayos"):
        try:
            datos = json.loads(arch.getvalue().decode("utf-8"))
            validos = [x for x in datos if isinstance(x, dict) and "id" in x and "secciones" in x]
            for x in validos:
                almacen.guardar(cod, x)
            st.success(f"Se importaron {len(validos)} ensayo(s).")
            st.rerun()
        except (ValueError, TypeError, UnicodeDecodeError):
            st.error("El archivo no es una copia válida de ENSAYA.")


# ---------------------------------------------------------------- Navegación
with st.sidebar:
    st.markdown("<h2 style='color:#1F5FBF;letter-spacing:.15em;margin:0'>ENSAYA</h2>", unsafe_allow_html=True)
    pag = st.radio("Navegación", PAGINAS, index=PAGINAS.index(S.pagina_v), label_visibility="collapsed")
    S.pagina_v = pag
    st.text_input("Código personal", key="codigo",
                  help="Identifica tu colección de ensayos. Usa uno que solo tú conozcas: quien lo escriba "
                       "podrá ver y editar esos trabajos.")

{"Inicio": inicio, "Editor": editor, "Mis trabajos": trabajos}[pag]()
