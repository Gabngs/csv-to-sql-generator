# CSV to SQL Insert Generator

Herramienta visual para convertir archivos CSV en sentencias SQL `INSERT` para MySQL, con mapeo automático de tablas y generación de campos del sistema (UUID, timestamps, IDs de usuario).

## 📋 Características

- ✅ **Interfaz gráfica nativa** (PySimpleGUI - sin HTML)
- ✅ **Seleccionar múltiples** archivos de una vez
- ✅ **Generación automática de campos del sistema**:
  - UUID generado por MySQL mediante función `UUID()`
  - Timestamp actual para `created_at` y `updated_at`
  - ID de usuario `created_by_id` y `updated_by_id` (configurable)
- ✅ **Mapeo automático** de tabla según nombre del archivo
- ✅ **Orden flexible de campos** - no importa el orden de las columnas
- ✅ **Funcionalidades útiles**:
  - Copiar INSERTs al portapapeles
  - Guardar en archivo .sql
  - Validación y mensajes de error claros

## 🚀 Instalación

### Requisitos

- Python 3.7+
- pip

### Pasos

1. **Clonar o descargar el repositorio**

```bash
git clone https://github.com/Gabngs/csv-to-sql-generator.git
cd csv-to-sql-generator
```

2. **Crear entorno virtual (opcional pero recomendado)**

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. **Instalar dependencias**

```bash
pip install -r requirements.txt
```

## 💻 Uso

### Ejecutar el programa

```bash
python csv_to_sql_uploader.py
```

### Pasos para usar la interfaz:

1. **Seleccionar archivos CSV**:
   - Haz clic en "Seleccionar" para buscar archivos
   - Puedes seleccionar múltiples archivos a la vez

2. **Procesar archivos**:
   - Haz clic en "Procesar Archivos"
   - El programa generará los INSERTs automáticamente

3. **Usar los resultados**:
   - **Copiar al portapapeles**: Copia todos los INSERTs para pegarlos en tu cliente SQL
   - **Guardar en archivo**: Guarda los INSERTs en un archivo .sql
   - **Limpiar**: Limpia la salida para procesar nuevos archivos

## 📁 Nombres de archivos esperados

El programa reconoce automáticamente estos nombres:

| Nombre archivo         | Tabla MySQL                 |
| ---------------------- | --------------------------- |
| `clasesgasto.csv`      | `catalogo_clasesgasto`      |
| `grupogasto.csv`       | `catalogo_grupogasto`       |
| `motivosgasto.csv`     | `catalogo_motivosgasto`     |
| `motivostipogasto.csv` | `catalogo_motivostipogasto` |
| `tiposgasto.csv`       | `catalogo_tiposgasto`       |

## 📋 Estructura del CSV

El CSV debe tener:

- **Primera fila**: nombres de columnas (cabeceras)
- **Filas siguientes**: datos

### Ejemplo (clasesgasto.csv)

```csv
"idclasesgasto","descripcion","activo","enviado"
"1","Costos Insumo y Menaje","1","0"
"2","Gastos Administrativos","1","0"
"3","Gastos Venta","1","0"
```

## 🔧 Configuración

Puedes modificar estos valores en `csv_to_sql_uploader.py`:

```python
# ID de usuario que realiza la operación
created_by_id = 184

# Agregar más tablas al mapeo TABLA_MAPEO
TABLA_MAPEO = {
    'clasesgasto': 'catalogo_clasesgasto',
    'grupogasto': 'catalogo_grupogasto',
    # ... más tablas
}

# Definir qué columnas esperar de cada tabla
COLUMNAS_CSV = {
    'catalogo_clasesgasto': ['idclasesgasto', 'descripcion', 'activo', 'enviado'],
    # ... más columnas
}
```

## 📊 Ejemplo de salida

**Entrada CSV:**

```csv
idclasesgasto,descripcion,activo,enviado
1,Costos Insumo y Menaje,1,0
```

**Salida SQL:**

```sql
INSERT INTO catalogo_clasesgasto (idclasesgasto, descripcion, activo, enviado, id, created_by_id, updated_by_id, created_at, updated_at)
VALUES ('1', 'Costos Insumo y Menaje', 1, 0, UUID(), 184, 184, '2026-05-20 15:30:45', '2026-05-20 15:30:45');
```

**Nota:** El campo `id` usa la función `UUID()` de MySQL que genera automáticamente un UUID único al momento de la inserción.

## 🗄️ Estructura de la base de datos

El programa genera INSERTs considerando esta estructura de tabla:

```sql
CREATE TABLE catalogo_clasesgasto (
    pkid BIGINT(20) PRIMARY KEY AUTO_INCREMENT,
    id VARCHAR(36) NOT NULL UNIQUE,
    idclasesgasto INT(11),
    descripcion VARCHAR(200),
    activo TINYINT(4) NOT NULL,
    enviado TINYINT(4),
    created_by_id BIGINT(20),
    updated_by_id BIGINT(20),
    deleted_by_id BIGINT(20) UNSIGNED,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP
);
```

**Nota:** El campo `pkid` se genera automáticamente (AUTO_INCREMENT), por lo que no se incluye en los INSERTs.

## ⚙️ Cómo funciona internamente

1. **Lee el CSV** y extrae cabeceras y datos
2. **Identifica la tabla** según el nombre del archivo
3. **Para cada fila**:
   - Toma los valores del CSV
   - Usa la función `UUID()` de MySQL para generar el `id` automáticamente
   - Usa timestamp actual para `created_at` y `updated_at`
   - Asigna `created_by_id` y `updated_by_id` a 999 -- valor editable --
   - Genera la sentencia INSERT

4. **Escapea valores** para evitar problemas con caracteres especiales
5. **Muestra los resultados** en la interfaz

## 🐛 Solución de problemas

### "No se reconoce el tipo de tabla"

- Verifica que el nombre del archivo sea exactamente uno de los reconocidos (sin espacios o caracteres especiales)
- Nombre debe estar en minúsculas

### "Error al leer CSV"

- Asegúrate que el archivo está en formato CSV válido
- Verifica la codificación del archivo (debe ser UTF-8)

### "Error en fila"

- Revisa que los valores del CSV sean válidos
- Busca caracteres especiales sin escapar

## 📝 Licencia

Este proyecto está disponible bajo la licencia MIT.

## 👨‍💻 Autor

Creado con Python y PySimpleGUI 
By GabNgs ( Neo )

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request
