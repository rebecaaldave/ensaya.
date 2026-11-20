# ENSAYA

Aplicación web en **Streamlit** para organizar, redactar y exportar ensayos académicos a Word (.docx).

## Funciones
- Datos generales, tipo de ensayo (7 tipos) y apartados editables (agregar o quitar).
- Generación de texto con IA a partir de tus notas, sin inventar fuentes, autores ni estadísticas.
- Formatos APA 7, MLA, Chicago y libre aplicados al documento Word y a la vista previa.
- Vista previa con edición y descarga en `.docx` real (python-docx).
- Mis trabajos: guardar, abrir, editar, eliminar, con copia de seguridad en JSON.

## Estructura
```
app.py            Interfaz y navegación
modelo.py         Tipos, plantillas, formatos y estructura del documento
ia.py             Llamada a la API de IA (clave en Secrets)
exportar.py       Generación del .docx
almacen.py        Persistencia en JSON (carpeta data/)
requirements.txt  Dependencias
.streamlit/config.toml            Tema blanco/azul/gris
.streamlit/secrets.toml.example   Ejemplo de secretos
```

## Ejecutar localmente
```
pip install -r requirements.txt
streamlit run app.py
```
Para usar la IA, crea `.streamlit/secrets.toml` (no se sube a GitHub) con:
```
ANTHROPIC_API_KEY = "tu-clave"
```

## Publicar en Streamlit Community Cloud
1. Sube todos los archivos a un repositorio de GitHub (el `.gitignore` excluye secretos y datos).
2. En https://share.streamlit.io elige **Create app**, selecciona el repositorio, la rama y el archivo principal `app.py`.
3. En **Advanced settings > Secrets** pega `ANTHROPIC_API_KEY = "tu-clave"` (opcional: `ANTHROPIC_MODEL`).
4. Pulsa **Deploy**.

## Notas importantes
- **Persistencia:** los ensayos se guardan en archivos JSON dentro de la app. En Community Cloud ese almacenamiento
  puede borrarse al reiniciar o redesplegar; usa «Descargar copia» en Mis trabajos para respaldarlos.
- **Código personal:** separa las colecciones de cada persona, pero no es una contraseña segura.
- **Referencias:** nunca las genera la IA; se usan las que tú escribas (ordenadas alfabéticamente en APA, MLA y Chicago).
- **Revisión:** verifica siempre el texto generado y los marcadores `[Agregar evidencia: ...]` antes de entregar.
