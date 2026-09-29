"""Precarga de datos de ejemplo en los archivos CSV de migrations/csv."""

from __future__ import annotations

from book_manager.entities.entities import (
    CotizacionDolar,
    Editorial,
    Genero,
    Libro,
    Moneda,
    Precio,
    Stock,
    TipoCotizacion,
    texto_a_fecha,
)
from book_manager.repositories.repositories import (
    CSV_DIR,
    ArchivoCSV,
    RepositorioLibro,
    crear_repositorios,
    vaciar_archivos,
)

GENEROS = [
    ("Novela", "Narrativa de ficción extensa"),
    ("Cuento", "Relatos breves de ficción"),
    ("Ensayo", "Textos de reflexión y análisis"),
    ("Poesía", "Obras de Poesía"),
    ("Infantil", "Libros Infantiles"),
    ("Juvenil", "Literatura para adolescentes"),
    ("Técnico", "Informática, Ciencia e Ingeniería"),
    ("Historia", "Historia Argentina y Universal"),
    ("Policial", "Novela de investigación policial y de misterio"),
    ("Ciencia ficción", "Futuros posibles"),
]

EDITORIALES = [
    ("Planeta", "España", "contacto@planeta.com.ar"),
    ("Penguin Random House", "Estados Unidos", "info@prh.example.com.ar"),
    ("Siglo XXI", "Argentina", "ventas@sigloxxi.example.com.ar"),
    ("Eudeba", "Argentina", "eudeba@eudeba.example.com.ar"),
    ("Anagrama", "España", "anagrama@anagrama.example.com.ar"),
    ("Salamandra", "España", "info@salamandra.example.com.ar"),
    ("Emecé", "Argentina", "emece@emece.example.com.ar"),
    ("Alfaguara", "España", "alfaguara@alfaguara.example.com.ar"),
    ("O'Reilly", "Estados Unidos", "orders@oreilly.example.com.ar"),
    ("Fondo de Cultura Económica", "México", "fce@fce.example.com.ar"),
]

MONEDAS = [
    ("ARS", "Peso argentino", "$", 1.0),
    ("USD", "Dólar estadounidense", "US$", 1.0),
    ("EUR", "Euro", "€", 1.17),
    ("BRL", "Real brasileño", "R$", 0.19),
    ("CLP", "Peso chileno", "CLP$", 0.00105),
    ("UYU", "Peso uruguayo", "$U", 0.025),
    ("GBP", "Libra esterlina", "£", 1.35),
    ("MXN", "Peso mexicano", "MX$", 0.054),
    ("JPY", "Yen japonés", "¥", 0.0068),
    ("PYG", "Guaraní paraguayo", "₲", 0.00014),
]

TIPOS_COTIZACION = [
    ("Oficial", "Dólar oficial minorista"),
    ("Blue", "Dólar informal"),
    ("MEP", "Dólar bolsa (Mercado Electrónico de Pagos)"),
    ("CCL", "Contado con liquidación"),
    ("Tarjeta", "Dólar para consumos con tarjeta"),
    ("Mayorista", "Dólar mayorista (BCRA)"),
    ("Cripto", "Dólar a través de stablecoins"),
    ("Ahorro", "Dólar para atesoramiento"),
    ("Turista", "Dólar para gastos en el exterior"),
    ("Importador", "Dólar para importación de bienes"),
]

LIBROS = [
    ("9789500705010", "Rayuela", "Julio Cortázar", 1963, 1, 8),
    ("9789875664998", "Ficciones", "Jorge Luis Borges", 1944, 2, 7),
    ("9789500426503", "Sobre héroes y tumbas", "Ernesto Sabato", 1961, 1, 1),
    ("9789876292015", "El eternauta", "H. G. Oesterheld", 1957, 10, 1),
    ("9789502307410", "Facundo", "Domingo F. Sarmiento", 1845, 8, 4),
    ("9789877383583", "Manuelita, ¿dónde vas?", "María Elena Walsh", 1997,
     5, 8),
    ("9781492056355", "Fluent Python", "Luciano Ramalho", 2022, 7, 9),
    ("9788433973412", "Nuestra parte de noche", "Mariana Enriquez", 2019,
     1, 5),
    ("9789871138128", "Operación masacre", "Rodolfo Walsh", 1957, 9, 3),
    ("9788498389234", "Harry Potter y la piedra filosofal", "J. K. Rowling",
     1997, 6, 6),
    ("9789505116465", "Veinte poemas de amor", "Pablo Neruda", 1924, 4, 2),
    ("9789682314223", "El laberinto de la soledad", "Octavio Paz", 1950,
     3, 10),
]

PRECIOS = [
    (1, "ARS", 32500.0), (2, "ARS", 28900.0), (3, "ARS", 31000.0),
    (4, "ARS", 45000.0), (5, "ARS", 18500.0), (6, "ARS", 15900.0),
    (7, "USD", 69.99), (8, "EUR", 24.90), (9, "ARS", 22000.0),
    (10, "EUR", 18.50), (11, "ARS", 14500.0), (12, "MXN", 320.0),
    (7, "ARS", 98000.0),
]

STOCK = [
    (1, 12, 5), (2, 8, 5), (3, 3, 4), (4, 20, 6), (5, 6, 3),
    (6, 15, 5), (7, 2, 3), (8, 9, 4), (9, 4, 4), (10, 25, 8),
    (11, 1, 2), (12, 7, 3),
]

COTIZACIONES = [
    ("Oficial", "2026-09-14", 1395.0, 1445.0),
    ("Oficial", "2026-09-15", 1400.0, 1450.0),
    ("Oficial", "2026-09-16", 1405.0, 1455.0),
    ("Oficial", "2026-09-17", 1410.0, 1460.0),
    ("Oficial", "2026-09-18", 1410.0, 1460.0),
    ("Blue", "2026-09-14", 1420.0, 1440.0),
    ("Blue", "2026-09-15", 1425.0, 1445.0),
    ("Blue", "2026-09-16", 1430.0, 1450.0),
    ("Blue", "2026-09-17", 1435.0, 1455.0),
    ("Blue", "2026-09-18", 1440.0, 1460.0),
    ("MEP", "2026-09-18", 1452.0, 1458.0),
    ("CCL", "2026-09-18", 1465.0, 1472.0),
]


def precargar_datos(directorio: str = CSV_DIR) -> None:
    """Vacía los CSV existentes y los genera de nuevo con los datos de ejemplo.

    Los datos se dan de alta a través de los repositorios, de modo que
    se aplican las mismas validaciones que en el uso normal del sistema.

    Args:
        directorio (str): Carpeta donde se guardan los CSV.
    """
    vaciar_archivos(directorio)

    repos = crear_repositorios(directorio)

    for nombre, descripcion in GENEROS:
        repos.generos.crear(Genero(0, nombre, descripcion))
    for nombre, pais, email in EDITORIALES:
        repos.editoriales.crear(Editorial(0, nombre, pais, email))
    for codigo, nombre, simbolo, equivalencia in MONEDAS:
        repos.monedas.crear(Moneda(0, codigo, nombre, simbolo, equivalencia))
    for nombre, descripcion in TIPOS_COTIZACION:
        repos.tipos_cotizacion.crear(TipoCotizacion(0, nombre, descripcion))

    for isbn, titulo, autor, anio, genero_id, editorial_id in LIBROS:
        repos.libros.crear(Libro(
            0, isbn, titulo, autor, anio,
            repos.generos.leer_por_id(genero_id),
            repos.editoriales.leer_por_id(editorial_id),
        ))

    monedas = {m.codigo: m for m in repos.monedas.leer_todos()}
    for libro_id, codigo, monto in PRECIOS:
        repos.precios.crear(Precio(
            0, repos.libros.leer_por_id(libro_id), monedas[codigo], monto
        ))

    for libro_id, cantidad, minimo in STOCK:
        repos.stock.crear(
            Stock(repos.libros.leer_por_id(libro_id), cantidad, minimo)
        )

    tipos = {t.nombre: t for t in repos.tipos_cotizacion.leer_todos()}
    for nombre, fecha, compra, venta in COTIZACIONES:
        repos.cotizaciones.crear(CotizacionDolar(
            tipos[nombre], texto_a_fecha(fecha), compra, venta
        ))


def hay_datos(directorio: str = CSV_DIR) -> bool:
    """Comprueba si ya hay libros cargados en los archivos CSV.

    Args:
        directorio (str): Carpeta donde se guardan los CSV.

    Returns:
        bool: True si el CSV de libros tiene al menos un registro.
    """
    archivo = ArchivoCSV(
        RepositorioLibro.ARCHIVO, RepositorioLibro.CAMPOS, directorio
    )
    return len(archivo.leer()) > 0


if __name__ == "__main__":
    precargar_datos()
    print(f"Datos precargados en {CSV_DIR}")
    