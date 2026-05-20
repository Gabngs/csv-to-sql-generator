import PySimpleGUI as sg
import csv
import uuid
from datetime import datetime
from pathlib import Path
import os

# Configurar tema
sg.theme('DarkBlue3')
sg.set_options(font=('Arial', 10))

# Mapeo de nombres de archivo a nombre de tabla
TABLA_MAPEO = {
    'clasesgasto': 'catalogo_clasesgasto',
    'grupogasto': 'catalogo_grupogasto',
    'motivosgasto': 'catalogo_motivosgasto',
    'motivostipogasto': 'catalogo_motivostipogasto',
    'tiposgasto': 'catalogo_tiposgasto',
}

# Columnas especiales por tabla (las que vienen del CSV)
COLUMNAS_CSV = {
    'catalogo_clasesgasto': ['idclasesgasto', 'descripcion', 'activo', 'enviado'],
    'catalogo_grupogasto': ['idgrupogasto', 'descripcion', 'activo', 'enviado'],
    'catalogo_motivosgasto': ['idmotivosgasto', 'descripcion', 'activo', 'enviado'],
    'catalogo_motivostipogasto': ['idmotivosgasto', 'idtipogasto', 'activo'],
    'catalogo_tiposgasto': ['idtipogasto', 'descripcion', 'activo', 'enviado'],
}

COLUMNAS_SISTEMA = ['id', 'created_by_id', 'updated_by_id', 'created_at', 'updated_at']

def obtener_nombre_tabla(filename):
    """Obtiene el nombre de tabla basado en el nombre del archivo"""
    nombre_base = Path(filename).stem.lower()
    return TABLA_MAPEO.get(nombre_base, None)

def leer_csv(filepath):
    """Lee el archivo CSV y retorna headers y filas"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            datos = list(reader)
        return headers, datos
    except Exception as e:
        return None, f"Error al leer CSV: {str(e)}"

def generar_insert(tabla, headers, fila):
    """Genera un INSERT SQL para una fila"""
    
    # Columnas del CSV
    columnas = COLUMNAS_CSV.get(tabla, headers)
    
    # Valores del CSV
    valores_csv = {}
    for col in columnas:
        if col in fila:
            valores_csv[col] = fila[col]
    
    # Generar valores del sistema
    id_uuid = str(uuid.uuid4())
    ahora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Construir lista de columnas y valores
    todas_columnas = []
    todos_valores = []
    
    # Agregar columnas del CSV
    for col in columnas:
        if col in valores_csv:
            todas_columnas.append(col)
            valor = valores_csv[col]
            
            # Escapar valor
            if valor is None or valor == '':
                todos_valores.append('NULL')
            elif col in ['activo', 'enviado']:
                todos_valores.append(str(valor))
            else:
                # Escapar comillas simples
                valor_escapado = str(valor).replace("'", "\\'")
                todos_valores.append(f"'{valor_escapado}'")
    
    # Agregar columnas del sistema
    todas_columnas.extend(['id', 'created_by_id', 'updated_by_id', 'created_at', 'updated_at'])
    todos_valores.extend([f"'{id_uuid}'", '184', '184', f"'{ahora}'", f"'{ahora}'"])
    
    # Construir INSERT
    columnas_str = ', '.join(todas_columnas)
    valores_str = ', '.join(todos_valores)
    
    insert = f"INSERT INTO {tabla} ({columnas_str}) VALUES ({valores_str});"
    
    return insert

def procesar_archivos(filepaths):
    """Procesa múltiples archivos y genera los INSERTs"""
    
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
        
        inserts_archivo = []
        for fila in datos:
            try:
                insert = generar_insert(tabla, headers, fila)
                inserts_archivo.append(insert)
            except Exception as e:
                errores.append(f"❌ {Path(filepath).name} - Error en fila: {str(e)}")
                continue
        
        todas_inserts.append({
            'archivo': Path(filepath).name,
            'tabla': tabla,
            'cantidad': len(inserts_archivo),
            'inserts': inserts_archivo
        })
    
    return todas_inserts, errores

# --- INTERFAZ GRÁFICA ---

layout = [
    [sg.Text('CSV to SQL Insert Generator', font=('Arial', 16, 'bold'))],
    [sg.Text('Selecciona múltiples archivos CSV para convertir a SQL INSERT', font=('Arial', 10))],
    [sg.Text('_' * 60)],
    
    # Área de selección de archivos
    [sg.InputText(
        'Haz clic en Seleccionar para elegir archivos CSV',
        key='-FILES-',
        disabled=True,
        size=(50, 1)
    ),
    sg.FilesBrowse('Seleccionar', file_types=(('CSV Files', '*.csv'), ('All Files', '*.*')), enable_events=True)],
    
    [sg.Text('_' * 60)],
    
    # Sección de resultados
    [sg.Multiline(
        size=(70, 20),
        key='-OUTPUT-',
        disabled=True,
        font=('Courier', 9),
        background_color='black',
        text_color='lime'
    )],
    
    [sg.Text('_' * 60)],
    
    # Botones
    [
        sg.Button('Procesar Archivos', size=(15, 1), button_color=('white', 'green')),
        sg.Button('Copiar al Portapapeles', size=(15, 1), button_color=('white', 'blue')),
        sg.Button('Guardar en Archivo', size=(15, 1), button_color=('white', 'orange')),
        sg.Button('Limpiar', size=(15, 1)),
        sg.Button('Salir', size=(15, 1), button_color=('white', 'red')),
    ],
    
    [sg.StatusBar('Listo', key='-STATUS-', size=(70, 1))],
]

# Crear ventana
window = sg.Window(
    'CSV to SQL Insert Generator',
    layout,
    finalize=True,
    size=(750, 700),
    icon=None
)

# Variables globales
archivos_seleccionados = []
inserts_generados = []

# --- LOOP PRINCIPAL ---
while True:
    event, values = window.read()
    
    if event == sg.WINDOW_CLOSED or event == 'Salir':
        break
    
    # Cuando se seleccionan archivos
    if values['-FILES-']:
        archivos_seleccionados = values['-FILES-'].split(';')
        archivos_seleccionados = [f.strip() for f in archivos_seleccionados if f.strip()]
        cantidad = len(archivos_seleccionados)
        window['-STATUS-'].update(f'✓ {cantidad} archivo(s) seleccionado(s)')
        window['-FILES-'].update(f'{cantidad} archivo(s) seleccionado(s)')
    
    if event == 'Procesar Archivos':
        if not archivos_seleccionados:
            sg.popup_error('Selecciona archivos CSV primero')
            continue
        
        window['-STATUS-'].update('Procesando...')
        window.refresh()
        
        # Procesar archivos
        inserts_generados, errores = procesar_archivos(archivos_seleccionados)
        
        # Mostrar resultados
        output = ""
        
        if errores:
            output += "⚠️  ERRORES:\n"
            for error in errores:
                output += f"{error}\n"
            output += "\n" + "=" * 70 + "\n\n"
        
        if inserts_generados:
            output += "✓ INSERTS GENERADOS:\n"
            output += "=" * 70 + "\n\n"
            
            total_inserts = 0
            for item in inserts_generados:
                output += f"📁 {item['archivo']} → {item['tabla']}\n"
                output += f"   Registros: {item['cantidad']}\n"
                output += "-" * 70 + "\n"
                output += "\n".join(item['inserts'])
                output += "\n\n"
                total_inserts += item['cantidad']
            
            output = f"TOTAL: {total_inserts} INSERT(s) generados\n\n" + output
        
        window['-OUTPUT-'].update(output)
        window['-STATUS-'].update(f'✓ Procesado: {sum(item["cantidad"] for item in inserts_generados)} registros')
    
    if event == 'Copiar al Portapapeles':
        texto = window['-OUTPUT-'].get()
        if texto:
            window.TKroot.clipboard_clear()
            window.TKroot.clipboard_append(texto)
            sg.popup_ok('✓ Copiado al portapapeles', title='Éxito')
        else:
            sg.popup_error('No hay contenido para copiar')
    
    if event == 'Guardar en Archivo':
        texto = window['-OUTPUT-'].get()
        if not texto:
            sg.popup_error('No hay contenido para guardar')
            continue
        
        filepath = sg.popup_get_file(
            'Guardar como...',
            save_as=True,
            file_types=(('SQL Files', '*.sql'), ('Text Files', '*.txt'), ('All Files', '*.*')),
            default_extension='.sql'
        )
        
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(texto)
                sg.popup_ok(f'✓ Guardado en:\n{filepath}', title='Éxito')
                window['-STATUS-'].update(f'✓ Archivo guardado: {filepath}')
            except Exception as e:
                sg.popup_error(f'Error al guardar: {str(e)}')
    
    if event == 'Limpiar':
        window['-OUTPUT-'].update('')
        window['-FILES-'].update('Haz clic en Seleccionar para elegir archivos CSV')
        archivos_seleccionados = []
        inserts_generados = []
        window['-STATUS-'].update('Listo')

window.close()
