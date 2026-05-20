# CSV to SQL Insert Generator

Herramienta visual para convertir archivos CSV en sentencias SQL `INSERT` para MySQL, con detección dinámica de columnas, configuración de campos por archivo y generación automática de campos del sistema (UUID, timestamps, IDs de usuario).

## Características

- **Interfaz gráfica nativa** (PySimpleGUI)
- **Selección múltiple** de archivos CSV en un solo paso
- **Detección dinámica de columnas**: lee los encabezados directamente de la primera fila del CSV, sin configuración manual por tabla
- **Configurador de campos por archivo**: antes de generar, elige qué columnas incluir, excluir o forzar a NULL
- **Generación automática de campos del sistema**:
  - `id` → `UUID()` (generado por MySQL)
  - `created_at` / `updated_at` → timestamp actual
  - `created_by_id` / `updated_by_id` → ID de usuario configurable
- **Mapeo automático** de nombre de archivo a nombre de tabla
- **Comentarios SQL preservados** (`--`) en la salida y en los archivos guardados
- **Exportar resultado**: copiar al portapapeles o guardar como `.sql`
- **Validación y mensajes de error** claros por archivo y por fila

## Instalación

### Requisitos

- Python 3.7+
- pip

### Pasos

```bash
git clone https://github.com/Gabngs/csv-to-sql-generator.git
cd csv-to-sql-generator
python -m venv venv
venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

## Uso

```bash
python csv_to_sql_uploader.py
```

### Flujo de trabajo

1. **Seleccionar** — elige uno o varios archivos CSV
2. **Configurar Campos** *(opcional)* — abre una ventana por cada archivo donde puedes:
   - Marcar / desmarcar columnas para incluirlas o excluirlas del INSERT
   - Activar **Forzar NULL** en columnas específicas (ignora el valor del CSV)
   - **Todo ON / Todo OFF** para selección rápida
3. **Procesar Archivos** — genera los INSERTs con la configuración activa
4. **Copiar al Portapapeles** o **Guardar en Archivo** para exportar el SQL

> Si no abres el configurador, se incluyen todas las columnas del CSV con sus valores originales.

## Nombres de archivos reconocidos

El mapeo de archivo → tabla es automático según el nombre del archivo:

| Nombre archivo         | Tabla MySQL                 |
| ---------------------- | --------------------------- |
| `clasesgasto.csv`      | `catalogo_clasesgasto`      |
| `grupogasto.csv`       | `catalogo_grupogasto`       |
| `motivosgasto.csv`     | `catalogo_motivosgasto`     |
| `motivostipogasto.csv` | `catalogo_motivostipogasto` |
| `tiposgasto.csv`       | `catalogo_tiposgasto`       |

Para agregar más tablas, edita `TABLA_MAPEO` en `csv_to_sql_uploader.py`.

## Estructura del CSV

- **Primera fila**: nombres de columnas (se usan tal cual, sin configuración adicional)
- **Filas siguientes**: datos

```csv
"idtiposgasto","idclasesgasto","descripcion","conautorizacion","activo","enviado"
"1","3","Adelanto Reserva","0","1","0"
```

## Ejemplo de salida

```sql
-- TOTAL: 1 INSERT(s) generados

-- ✓ INSERTS GENERADOS:
-- ======================================================================

-- 📁 tiposgasto.csv → catalogo_tiposgasto
--    Registros: 1
-- ----------------------------------------------------------------------
INSERT INTO catalogo_tiposgasto (idtiposgasto, idclasesgasto, descripcion, conautorizacion, activo, enviado, id, created_by_id, updated_by_id, created_at, updated_at) VALUES ('1', '3', 'Adelanto Reserva', 0, 1, 0, UUID(), 184, 184, '2026-05-20 15:30:45', '2026-05-20 15:30:45');
```

## Configuración

Edita estas constantes en `csv_to_sql_uploader.py`:

```python
# Mapeo archivo → tabla (agrega los que necesites)
TABLA_MAPEO = {
    'clasesgasto': 'catalogo_clasesgasto',
    ...
}

# Columnas que siempre se tratan como texto aunque el valor parezca número
COLUMNAS_TEXTO = {'descripcion', 'descpers', 'nombre'}
```

El `created_by_id` / `updated_by_id` se ajusta cambiando el valor `184` en `generar_insert`.

## Cómo funciona internamente

1. Lee el CSV y extrae encabezados y filas
2. Mapea el nombre del archivo al nombre de tabla
3. Aplica la configuración de campos (si fue definida por el usuario)
4. Por cada fila:
   - Incluye las columnas activas con su valor o NULL según configuración
   - Agrega los campos del sistema al final
5. Escapa valores para evitar problemas con comillas y caracteres especiales
6. Muestra el resultado en la interfaz; el texto se preserva íntegro al copiar/guardar

## Solución de problemas

| Error | Causa probable |
|---|---|
| "No se reconoce el tipo de tabla" | El nombre del archivo no coincide con ninguna entrada en `TABLA_MAPEO` |
| "Error al leer CSV" | Archivo no es CSV válido o no está en UTF-8 |
| "Error en fila" | Valor inesperado en una celda; revisa caracteres especiales |

## Roadmap

- [x] Interfaz gráfica nativa sin dependencias web
- [x] Selección múltiple de archivos
- [x] Generación automática de campos del sistema (UUID, timestamps)
- [x] Detección dinámica de columnas desde el encabezado del CSV
- [x] Interfaz para configurar campos dinámicamente (incluir / excluir / forzar NULL)
- [x] Validación de datos y reporte de errores por archivo y fila
- [x] Vista previa del SQL generado antes de exportar
- [x] Comentarios SQL (`--`) preservados correctamente en archivo guardado
- [ ] Configurar `created_by_id` desde la interfaz sin tocar el código
- [ ] Soporte para encodings adicionales (Latin-1, Windows-1252)
- [ ] Soporte para separadores personalizados (`;`, `\t`, `|`)
- [ ] Generación de sentencias `UPDATE` además de `INSERT`
- [ ] Exportar / importar configuración de campos guardada como JSON
- [ ] Vista previa de los datos del CSV en tabla antes de procesar
- [ ] Validación de tipos de dato por columna (longitud máxima, formato fecha, etc.)
- [ ] Modo batch por carpeta: procesar todos los CSV de un directorio

## Licencia

MIT

## Autor

By GabNgs ( Neo )
