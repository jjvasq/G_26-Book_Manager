# Changelog

# Sprint 3

## [Ejercicio 02]
- Se agrega en `migrations.py` la función `cargar_datos_sql`, que ejecuta en
orden las sentencias de los archivos `.sql` de `migrations/sql` en una
única transacción y devuelve los registros insertados por archivo.
- Se agregan `leer_sentencias_sql` y `archivos_sql`.
- `main` carga los datos iniciales desde los `.sql`, si todavía no existen,
migra los CSV del Sprint 1.

## [Ejercicio 01]
- Se crea la rama `Sprint_3` a partir de `Sprint_2`.
- Se agregan las carpetas `scraper` (proyecto Scrapy) y `reportes` (alertas
CSV y reportes Excel generados, que no se versionan).
- Se agregan `scrapy` y `openpyxl` a `requirements.txt`.
- Se actualiza el README con el objetivo y el contexto del Sprint 3.

# Sprint 2 - Correcciones de la devolución

- `obtener_cotizaciones` ya no descarta las casas de DolarApi cuyo tipo no
está registrado: da de alta el tipo de cotización y registra su cotización.
- La fecha de la cotización se convierte de UTC a la hora de Argentina (antes
una consulta nocturna podía quedar con la fecha del día siguiente).
- La migración ya no borra ni recrea las tablas: crea solo las que faltan.
- Cada sentencia generada es `INSERT ... ON CONFLICT DO NOTHING`: la
migración se puede repetir sin duplicar registros ni perder los datos
cargados después (altas, modificaciones y borrados lógicos).
- Se versionan los CSV del Sprint 1 en `migrations/csv`.
- Se regeneran los archivos `.sql` de `migrations/sql`.
- `main` ya no muestra la cadena de conexión al informar la migración.
- Se quitan los índices simples de `isbn` y `codigo`, que quedan cubiertos
por los índices únicos.
- Se deja de versionar el archivo `.env` (se agrega a `.gitignore`).
- Se versiona la plantilla `.env.example` sin datos de conexión reales.
- Se actualiza el README con los pasos para crear el `.env` a partir de la
plantilla.

# Sprint 2

## [Ejercicio 08]
- Se agrega en el menú *Valor del dólar* la opción "Obtener las cotizaciones
por API", que usa en `obtener_cotizaciones()`.
- Se agrega en el menú *Lista de precios* la opción "Lista de precios
bimonetaria": muestra cada libro en pesos y en la moneda elegida, según el
tipo de moneda seleccionada.
- Se agrega en el menú *Lista de precios* la opción "Exportar precios a CSV",
que genera un archivo con el precio de cada libro en todas las monedas.
- Se agregan en `ServicioReportes` los métodos `precio_en_moneda`,
`lista_bimonetaria` y `exportar_precios_csv`.
- Se actualiza el README con la configuración del `.env`.
- Se agregan excepciones.
- Se modifica el formato de la interfaz de la consola.

## [Ejercicio 07]
- Se agrega `API_URL` al archivo `.env`.
- Al servicio de cotizaciones le cambiamos el nombre a
`ServicioCotizacionDolar`.
- Cambia el nombre de  `actualizar_desde_api()` a `obtener_cotizaciones()`,
que busca y descarga las cotizaciones de DolarApi y las registra en
la base de datos.

## [Ejercicio 06]
- Se reemplazan los repositorios CSV por repositorios sobre la base de datos
(`RepositorioSQL` genérico y uno por entidad), manteniendo las interfaces
`IRepositorio`, `IRepositorioStock` e `IRepositorioCotizacionDolar`.
- Cada operación usa el context manager de transacciones y convierte los
modelos ORM en entidades del dominio.
- Se mantiene el borrado lógico con la columna `estado`.
- `crear_repositorios` recibe la conexión a la base de datos.
- La precarga de datos de ejemplo (`preload_data.py`) ahora carga la base de
datos en lugar de los CSV.

## [Ejercicio 05]
- Se crea `migrations/migrations.py` con la función
`migrar_datos(carpeta_csvs, carpeta_sqls)`.
- Se leen los CSV del Sprint 1 y, por cada tabla, se genera un archivo `.sql`
con las sentencias `INSERT` en `migrations/sql` (numerados según el orden de
las claves foráneas).
- Las sentencias se ejecutan en una única transacción: si una falla no se
guarda ningún dato.
- Se conservan los ID y el `estado` (borrado lógico) de cada registro.
- `main.py` migra los datos automáticamente si la base está vacía, o siempre
con `main(import_default_data=True)`.

## [Ejercicio 04]
- Se crean los modelos ORM en `models/models.py`: `generos`, `editoriales`,
`monedas`, `tipos_cotizacion`, `libros`, `precios`, `stock` y
`cotizaciones_dolar`.
- Se definen claves foráneas y relaciones (`relationship`) entre libros,
géneros, editoriales, precios, monedas, stock y cotizaciones.
- `stock` usa como clave primaria el ID del libro y `cotizaciones_dolar` una
clave compuesta (tipo, fecha), igual que en el Sprint 1.
- Se agregan restricciones `CHECK` (montos y cotizaciones positivos, stock no
negativo) y la columna `estado` para el borrado lógico.
- Se agregan las funciones `crear_tablas` y `eliminar_tablas`.

## [Ejercicio 03]
- Se crea el context manager `Transaccion` (métodos `__enter__` y
`__exit__`) para manejar las transacciones.
- Si el bloque `with` termina sin errores se hace `commit`. Si se produce
una excepción se hace `rollback` y la excepción se propaga. La sesión se
cierra siempre.
- Se agrega el método `ConexionDB.transaccion()` que devuelve el context
manager.

## [Ejercicio 02]
- Se crea la clase `ConexionDB` en `database/connection.py`, que administra
el engine y las sesiones de SQLAlchemy sobre la base PostgreSQL de Supabase.
- La URL de conexión (`DATABASE_URL`) se guarda en el `.env` tal como la da
Supabase (Connect > ORM > `DIRECT_URL`), con el marcador `[YOUR-PASSWORD]`.
- `probar()` verifica la conexión consultando `SELECT version();`.
- Se agregan `SQLAlchemy`, `python-dotenv` y `psycopg2-binary` a
`requirements.txt`.

## [Ejercicio 01]
- Se crea la rama `Sprint_2` a partir de la rama `Sprint_1`.
- Se agregan las carpetas `database`, `models`, `migrations/sql`.
- Se crea el archivo `.env` en la raíz del proyecto.
- Se actualiza el README con el objetivo y el contexto del Sprint 2.

# Sprint 1

## [Ejercicio 07]
- Se crea `main.py` con la función `main(import_default_data)`.
- La precarga de datos se ejecuta automáticamente si no hay datos cargados, con
 `main(import_default_data=True)` se regeneran los datos de ejemplo.

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
