# Changelog

Todos los cambios notables en este proyecto se documentarán en este archivo.

## [1.0.0] - 2026-05-20

### Agregado
- Interfaz gráfica con PySimpleGUI
- Soporte para arrastrar y soltar archivos CSV
- Selección múltiple de archivos
- Generación automática de UUIDs para campo `id`
- Generación automática de timestamps para `created_at` y `updated_at`
- Mapeo automático de tablas según nombre de archivo
- Funcionalidad de copiar al portapapeles
- Funcionalidad de guardar en archivo .sql
- Validación de archivos y mensajes de error claros

### Características soportadas
- Tabla: `catalogo_clasesgasto`
- Tabla: `catalogo_grupogasto`
- Tabla: `catalogo_motivosgasto`
- Tabla: `catalogo_motivostipogasto`
- Tabla: `catalogo_tiposgasto`

## Roadmap futuro

- [ ] Agregar más tablas de catálogo
- [ ] Interfaz para configurar campos dinámicamente
- [ ] Validación de datos antes de generar INSERTs
- [ ] Vista previa de datos
- [ ] Soporte para otras bases de datos (PostgreSQL, SQLite)
- [ ] Tests automatizados
