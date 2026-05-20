import PySimpleGUI as sg
import csv
from datetime import datetime
from pathlib import Path

sg.theme('DarkBlue3')
sg.set_options(font=('Arial', 10))

TABLA_MAPEO = {
    'clasesgasto': 'catalogo_clasesgasto',
    'grupogasto': 'catalogo_grupogasto',
    'motivosgasto': 'catalogo_motivosgasto',
    'motivostipogasto': 'catalogo_motivostipogasto',
    'tiposgasto': 'catalogo_tiposgasto',
}

COLUMNAS_TEXTO = {'descripcion', 'descpers', 'nombre'}


def obtener_nombre_tabla(filename):
    nombre_base = Path(filename).stem.lower()
    return TABLA_MAPEO.get(nombre_base, None)


def leer_csv(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            datos = list(reader)
        return headers, datos
    except Exception as e:
        return None, f"Error al leer CSV: {str(e)}"


def _formatear_valor(col, valor):
    if valor is None or valor == '':
        return 'NULL'
    col_lower = col.lower()
    if col_lower.startswith('id') or col_lower in COLUMNAS_TEXTO or 'desc' in col_lower or 'nombre' in col_lower:
        return "'" + str(valor).replace("'", "\\'") + "'"
    try:
        int_val = int(valor)
        if str(int_val) == str(valor).strip():
            return str(int_val)
    except (ValueError, TypeError):
        pass
    return "'" + str(valor).replace("'", "\\'") + "'"


def generar_insert(tabla, headers, fila, config_campos=None):
    ahora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    columnas = []
    valores = []

    for col in headers:
        if config_campos:
            cfg = config_campos.get(col, {'incluir': True, 'forzar_null': False})
            if not cfg['incluir']:
                continue
            columnas.append(col)
            valores.append('NULL' if cfg['forzar_null'] else _formatear_valor(col, fila.get(col, '')))
        else:
            columnas.append(col)
            valores.append(_formatear_valor(col, fila.get(col, '')))

    columnas += ['id', 'created_by_id', 'updated_by_id', 'created_at', 'updated_at']
    valores += ['UUID()', '184', '184', f"'{ahora}'", f"'{ahora}'"]

    return f"INSERT INTO {tabla} ({', '.join(columnas)}) VALUES ({', '.join(valores)});"


def procesar_archivos(filepaths, config_global=None):
    todas_inserts = []
    errores = []

    for filepath in filepaths:
        if not filepath.endswith('.csv'):
            errores.append(f"❌ {Path(filepath).name} - No es un archivo CSV")
            continue

        tabla = obtener_nombre_tabla(filepath)
        if not tabla:
            errores.append(f"❌ {Path(filepath).name} - No se reconoce el tipo de tabla")
            continue

        headers, datos = leer_csv(filepath)
        if headers is None:
            errores.append(f"❌ {Path(filepath).name} - {datos}")
            continue

        config_campos = config_global.get(filepath) if config_global else None

        inserts_archivo = []
        for fila in datos:
            try:
                insert = generar_insert(tabla, headers, fila, config_campos)
                inserts_archivo.append(insert)
            except Exception as e:
                errores.append(f"❌ {Path(filepath).name} - Error en fila: {str(e)}")
                continue

        todas_inserts.append({
            'archivo': Path(filepath).name,
            'tabla': tabla,
            'cantidad': len(inserts_archivo),
            'inserts': inserts_archivo,
        })

    return todas_inserts, errores


def construir_sql(lista_inserts, lista_errores):
    """Construye el texto SQL final con comentarios -- garantizados."""
    lineas = []

    if lista_errores:
        lineas.append("-- ⚠️  ERRORES:")
        for error in lista_errores:
            lineas.append(f"-- {error}")
        lineas.append("")
        lineas.append("-- " + "=" * 70)
        lineas.append("")

    if lista_inserts:
        total = sum(item['cantidad'] for item in lista_inserts)
        lineas.append(f"-- TOTAL: {total} INSERT(s) generados")
        lineas.append("")
        lineas.append("-- ✓ INSERTS GENERADOS:")
        lineas.append("-- " + "=" * 70)
        lineas.append("")

        for item in lista_inserts:
            lineas.append(f"-- 📁 {item['archivo']} → {item['tabla']}")
            lineas.append(f"--    Registros: {item['cantidad']}")
            lineas.append("-- " + "-" * 70)
            lineas.extend(item['inserts'])
            lineas.append("")
            lineas.append("")

    return "\n".join(lineas)


TITULO_CONFIG = 'Configurar Campos'


def _frame_archivo(fi, datos, col_mapping):
    """Construye el frame de columnas para un archivo CSV."""
    filepath = datos['filepath']
    headers = datos['headers']
    filename = Path(filepath).name
    tabla = datos['tabla']

    col_rows = [
        [
            sg.Text('Incluir', size=(6, 1), font=('Arial', 9, 'bold')),
            sg.Text('Columna', size=(24, 1), font=('Arial', 9, 'bold')),
            sg.Text('Forzar NULL', size=(11, 1), font=('Arial', 9, 'bold')),
        ],
        [sg.HSeparator()],
    ]
    for ci, col in enumerate(headers):
        col_mapping[(fi, ci)] = (filepath, col)
        col_rows.append([
            sg.Checkbox('', default=True, key=f'-INC-{fi}-{ci}-', enable_events=True, pad=(4, 2)),
            sg.Text(col, size=(24, 1), font=('Courier', 9)),
            sg.Checkbox('', default=False, key=f'-NUL-{fi}-{ci}-', pad=(4, 2)),
        ])

    frame_height = min(220, 28 * len(headers) + 50)
    inner = sg.Column(col_rows, scrollable=True, vertical_scroll_only=True, size=(400, frame_height))
    return [sg.Frame(f'  {filename}  →  {tabla}  ', [[inner]], font=('Arial', 10, 'bold'))]


def _toggle_todos(win, col_mapping, habilitar):
    """Activa o desactiva todos los checkboxes Incluir y ajusta NULL."""
    for (fi, ci) in col_mapping:
        win[f'-INC-{fi}-{ci}-'].update(habilitar)
        win[f'-NUL-{fi}-{ci}-'].update(disabled=not habilitar)


def _extraer_config(col_mapping, vals):
    """Construye el dict de configuración desde los valores del formulario."""
    config = {}
    for (fi, ci), (filepath, col) in col_mapping.items():
        if filepath not in config:
            config[filepath] = {}
        config[filepath][col] = {
            'incluir': vals.get(f'-INC-{fi}-{ci}-', True),
            'forzar_null': vals.get(f'-NUL-{fi}-{ci}-', False),
        }
    return config


def abrir_configuracion_campos(archivos_datos):
    """
    archivos_datos: list of {'filepath': str, 'tabla': str, 'headers': list}
    Returns: {filepath: {col: {'incluir': bool, 'forzar_null': bool}}} or None si se cancela
    """
    col_mapping = {}
    frames = [_frame_archivo(fi, d, col_mapping) for fi, d in enumerate(archivos_datos)]
    outer_col = sg.Column(frames, scrollable=True, vertical_scroll_only=True, size=(460, 460))

    layout = [
        [sg.Text(TITULO_CONFIG, font=('Arial', 14, 'bold'))],
        [sg.Text('Incluir: el campo entra al INSERT con su valor del CSV.', font=('Arial', 9))],
        [sg.Text('Forzar NULL: el campo entra al INSERT pero con valor NULL.', font=('Arial', 9))],
        [sg.HSeparator()],
        [outer_col],
        [sg.HSeparator()],
        [
            sg.Button('Aplicar', size=(10, 1), button_color=('white', 'green')),
            sg.Button('Todo ON', size=(9, 1)),
            sg.Button('Todo OFF', size=(9, 1)),
            sg.Button('Cancelar', size=(10, 1), button_color=('white', 'red')),
        ],
    ]

    win = sg.Window(TITULO_CONFIG, layout, modal=True, finalize=True, size=(490, 620))

    while True:
        ev, vals = win.read()

        if ev in (sg.WINDOW_CLOSED, 'Cancelar'):
            win.close()
            return None

        if ev == 'Todo ON':
            _toggle_todos(win, col_mapping, True)
        elif ev == 'Todo OFF':
            _toggle_todos(win, col_mapping, False)
        elif isinstance(ev, str) and ev.startswith('-INC-'):
            parts = ev.split('-')
            win[f'-NUL-{parts[2]}-{parts[3]}-'].update(disabled=not vals[ev])
        elif ev == 'Aplicar':
            config = _extraer_config(col_mapping, vals)
            win.close()
            return config


# --- INTERFAZ GRÁFICA ---

layout = [
    [sg.Text('CSV to SQL Insert Generator', font=('Arial', 16, 'bold'))],
    [sg.Text('Selecciona múltiples archivos CSV para convertir a SQL INSERT', font=('Arial', 10))],
    [sg.Text('_' * 60)],

    [
        sg.InputText(
            'Haz clic en Seleccionar para elegir archivos CSV',
            key='-FILES-',
            disabled=True,
            size=(50, 1),
        ),
        sg.FilesBrowse('Seleccionar', file_types=(('CSV Files', '*.csv'), ('All Files', '*.*')), enable_events=True),
    ],

    [sg.Text('_' * 60)],

    [sg.Multiline(
        size=(70, 20),
        key='-OUTPUT-',
        disabled=True,
        font=('Courier', 9),
        background_color='black',
        text_color='lime',
    )],

    [sg.Text('_' * 60)],

    [
        sg.Button(TITULO_CONFIG, size=(15, 1), button_color=('white', '#5a5a8a')),
        sg.Button('Procesar Archivos', size=(15, 1), button_color=('white', 'green')),
        sg.Button('Limpiar', size=(10, 1)),
    ],
    [
        sg.Button('Copiar al Portapapeles', size=(18, 1), button_color=('white', 'blue')),
        sg.Button('Guardar en Archivo', size=(15, 1), button_color=('white', 'orange')),
        sg.Button('Salir', size=(10, 1), button_color=('white', 'red')),
    ],

    [sg.StatusBar('Listo', key='-STATUS-', size=(70, 1))],
]

window = sg.Window(
    'CSV to SQL Insert Generator',
    layout,
    finalize=True,
    size=(750, 730),
    icon=None,
)

archivos_seleccionados = []
inserts_generados = []
errores_generados = []
config_campos_global = {}

# --- LOOP PRINCIPAL ---
while True:
    event, values = window.read()

    if event == sg.WINDOW_CLOSED or event == 'Salir':
        break

    files_val = values.get('-FILES-', '')
    if files_val and ('\\' in files_val or '/' in files_val or ':' in files_val):
        archivos_seleccionados = files_val.split(';')
        archivos_seleccionados = [f.strip() for f in archivos_seleccionados if f.strip()]
        config_campos_global = {}
        cantidad = len(archivos_seleccionados)
        window['-STATUS-'].update(f'✓ {cantidad} archivo(s) — configura campos o procesa directamente')
        window['-FILES-'].update(f'{cantidad} archivo(s) seleccionado(s)')

    if event == TITULO_CONFIG:
        if not archivos_seleccionados:
            sg.popup_error('Selecciona archivos CSV primero')
            continue

        archivos_datos = []
        for filepath in archivos_seleccionados:
            if not filepath.endswith('.csv'):
                continue
            tabla = obtener_nombre_tabla(filepath)
            if not tabla:
                continue
            headers, _ = leer_csv(filepath)
            if headers is None:
                continue
            archivos_datos.append({'filepath': filepath, 'tabla': tabla, 'headers': headers})

        if not archivos_datos:
            sg.popup_error('No se pudieron leer los archivos CSV seleccionados')
            continue

        resultado = abrir_configuracion_campos(archivos_datos)
        if resultado is not None:
            config_campos_global = resultado
            window['-STATUS-'].update('✓ Configuración de campos aplicada — listo para procesar')

    if event == 'Procesar Archivos':
        if not archivos_seleccionados:
            sg.popup_error('Selecciona archivos CSV primero')
            continue

        window['-STATUS-'].update('Procesando...')
        window.refresh()

        inserts_generados, errores_generados = procesar_archivos(
            archivos_seleccionados,
            config_campos_global if config_campos_global else None,
        )

        # El display puede mostrar sin -- por limitaciones del widget; los archivos siempre se generan correctamente
        display = construir_sql(inserts_generados, errores_generados)
        window['-OUTPUT-'].update(display)
        window['-STATUS-'].update(f'✓ Procesado: {sum(item["cantidad"] for item in inserts_generados)} registros')

    if event == 'Copiar al Portapapeles':
        if not inserts_generados and not errores_generados:
            sg.popup_error('No hay contenido para copiar')
            continue
        # Reconstruye desde los datos originales — garantiza -- en el output
        contenido = construir_sql(inserts_generados, errores_generados)
        window.TKroot.clipboard_clear()
        window.TKroot.clipboard_append(contenido)
        sg.popup_ok('✓ Copiado al portapapeles', title='Éxito')

    if event == 'Guardar en Archivo':
        if not inserts_generados and not errores_generados:
            sg.popup_error('No hay contenido para guardar')
            continue

        filepath = sg.popup_get_file(
            'Guardar como...',
            save_as=True,
            file_types=(('SQL Files', '*.sql'), ('Text Files', '*.txt'), ('All Files', '*.*')),
            default_extension='.sql',
        )

        if filepath:
            try:
                # Reconstruye desde los datos originales — garantiza -- en el output
                contenido = construir_sql(inserts_generados, errores_generados)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(contenido)
                sg.popup_ok(f'✓ Guardado en:\n{filepath}', title='Éxito')
                window['-STATUS-'].update(f'✓ Archivo guardado: {filepath}')
            except Exception as e:
                sg.popup_error(f'Error al guardar: {str(e)}')

    if event == 'Limpiar':
        window['-OUTPUT-'].update('')
        window['-FILES-'].update('Haz clic en Seleccionar para elegir archivos CSV')
        archivos_seleccionados = []
        inserts_generados = []
        errores_generados = []
        config_campos_global = {}
        window['-STATUS-'].update('Listo')

window.close()
