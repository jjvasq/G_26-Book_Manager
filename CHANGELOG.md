# Changelog

## [Ejercicio 06]
- Se crea la interfaz de consola con menús de CRUD para cada Entidad.
- Se agregan movimientos de stock, histórico de cotizaciones y reportes.
- Si DolarApi no responde, la consola pide las cotizaciones para ingresarlas 
manualmente y las registra con `registrar_manual`.

## [Ejercicio 05]
- Se crea `preload_data.py` con al menos 10 registros por Entidad.
- Se generan los archivos CSV en `migrations/csv`.
- En la precarga se vacían los CSV antes de cargar los datos.

## [Ejercicio 04]
- Se crean los servicios con validaciones de negocio (unicidad, integridad 
referencial).
- Se agrega la conversión de precios a pesos y la consulta a dolarapi.com.
- Si no se puede consultar la API, se le pide la cotización al usuario para 
cargarla manualmente.
- Se agregan reportes de inventario valorizado, stock bajo mínimo y cotización 
de libros.
- Los reportes actualizan las cotizaciones desde DolarApi; si no hay conexión, 
usan la última cotización guardada.
- Se agregan verificaciones que la consola usa antes de crear o modificar 
(`verificar_nombre`, `verificar_codigo`, `verificar_isbn`, `verificar_moneda`, 
`verificar_sin_stock`, `verificar_fecha`).
- No se permite cargar dos cotizaciones del mismo tipo en la misma fecha.

## [Ejercicio 03]
- Se crean las interfaces de repositorio y su implementación en CSV.
- Se agregan los repositorios de Stock y CotizacionDolar con claves propias.
- Se implementa el borrado lógico: los CSV tienen la columna `estado` 
(1 = activo, 0 = borrado).

## [Ejercicio 02]
- Se crean las entidades Libro, Genero, Editorial, Moneda, TipoCotizacion, 
Precio, Stock y CotizacionDolar.
- Se aplica encapsulamiento con atributos privados y propiedades con validación

## [Ejercicio 01]
- Se inicializa el repositorio y la rama `Sprint_1`.
- Se crea la estructura de directorios del proyecto.
