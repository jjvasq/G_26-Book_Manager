"""Estilos de la consola: menús, tablas, mensajes y preguntas con Rich.

Este módulo concentra todo lo "visual" de la interfaz. La clase Consola
solo decide QUÉ mostrar y llama a estas funciones para decidir CÓMO se ve.
Rich funciona igual en una terminal y en un notebook de Colab/Jupyter.
"""

from __future__ import annotations

import re
from typing import Callable, Iterable, List, Sequence, Tuple

from rich import box
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

from book_manager.entities.entities import (
    CotizacionDolar,
    Editorial,
    Genero,
    Libro,
    Moneda,
    Precio,
    Stock,
    TipoCotizacion,
)

# Paleta de la aplicación: se cambia acá y se aplica en toda la consola.
# Los colores son tonos medios que contrastan tanto con un fondo oscuro
# como con uno claro, porque no sabemos qué tema usa cada terminal. Por
# eso tampoco se fija un color de fondo ni blanco/negro para el texto
# principal: "titulo" usa el color de texto propio de la terminal.
TEMA = Theme({
    "titulo": "bold",
    "acento": "bold #4f7fe0",
    "suave": "#808080",
    "numero": "bold #b87700",
    "ok": "bold #2b9443",
    "error": "bold #e0405a",
    "aviso": "#b87700",
    "info": "#1a8bab",
    "fila_par": "#4f7fe0",
})

consola = Console(theme=TEMA, highlight=False)

# Columnas de la tabla de cada entidad: (encabezado, función, alineación).
Columna = Tuple[str, Callable[[object], object], str]

COLUMNAS: dict[type, List[Columna]] = {
    Libro: [
        ("ID", lambda l: l.id, "right"),
        ("Título", lambda l: l.titulo, "left"),
        ("Autor", lambda l: l.autor, "left"),
        ("Año", lambda l: l.anio, "right"),
        ("ISBN", lambda l: l.isbn, "left"),
        ("Género", lambda l: l.genero.nombre, "left"),
        ("Editorial", lambda l: l.editorial.nombre, "left"),
    ],
    Genero: [
        ("ID", lambda g: g.id, "right"),
        ("Nombre", lambda g: g.nombre, "left"),
        ("Descripción", lambda g: g.descripcion, "left"),
    ],
    TipoCotizacion: [
        ("ID", lambda t: t.id, "right"),
        ("Nombre", lambda t: t.nombre, "left"),
        ("Descripción", lambda t: t.descripcion, "left"),
    ],
    Editorial: [
        ("ID", lambda e: e.id, "right"),
        ("Nombre", lambda e: e.nombre, "left"),
        ("País", lambda e: e.pais, "left"),
        ("Email", lambda e: e.email, "left"),
    ],
    Moneda: [
        ("ID", lambda m: m.id, "right"),
        ("Código", lambda m: m.codigo, "left"),
        ("Nombre", lambda m: m.nombre, "left"),
        ("Símbolo", lambda m: m.simbolo, "center"),
        ("1 unidad en USD", lambda m: f"{m.equivalencia_usd:g}", "right"),
    ],
    Precio: [
        ("ID", lambda p: p.id, "right"),
        ("Libro", lambda p: p.libro.titulo, "left"),
        ("Moneda", lambda p: p.moneda.codigo, "center"),
        ("Monto", lambda p: f"{p.moneda.simbolo} {p.monto:,.2f}", "right"),
    ],
    Stock: [
        ("ID libro", lambda s: s.libro_id, "right"),
        ("Libro", lambda s: s.libro.titulo, "left"),
        ("Cantidad", lambda s: s.cantidad, "right"),
        ("Mínimo", lambda s: s.stock_minimo, "right"),
        ("Estado", lambda s: (
            Text("● reponer", style="error") if s.bajo_minimo
            else Text("● ok", style="ok")
        ), "left"),
    ],
    CotizacionDolar: [
        ("Fecha", lambda c: c.fecha, "left"),
        ("Tipo", lambda c: c.tipo.nombre, "left"),
        ("Compra", lambda c: f"$ {c.compra:,.2f}", "right"),
        ("Venta", lambda c: f"$ {c.venta:,.2f}", "right"),
    ],
}


def _celda(valor: object) -> object:
    """Convierte un valor en algo que Rich pueda poner en una celda."""
    return valor if isinstance(valor, Text) else Text(str(valor))


def nueva_tabla(titulo: str = "", *encabezados: Tuple[str, str]) -> Table:
    """Crea una tabla con el estilo de la aplicación.

    Args:
        titulo (str): Título que se muestra arriba de la tabla.
        *encabezados (Tuple[str, str]): Pares (texto, alineación).

    Returns:
        Table: Tabla vacía lista para agregarle filas.
    """
    tabla = Table(
        title=titulo or None, title_style="acento", title_justify="left",
        box=box.ROUNDED, border_style="suave", header_style="acento",
        row_styles=["", "fila_par"], caption_style="suave",
        caption_justify="left",
    )
    for texto, alineacion in encabezados:
        tabla.add_column(texto, justify=alineacion)
    return tabla


def tabla_de(items: Sequence[object]) -> Table | None:
    """Arma una tabla con columnas según el tipo de los objetos.

    Args:
        items (Sequence[object]): Objetos de una misma entidad.

    Returns:
        Table | None: La tabla, o None si el tipo no tiene columnas
            definidas en COLUMNAS.
    """
    columnas = COLUMNAS.get(type(items[0]))
    if columnas is None:
        return None
    tabla = nueva_tabla("", *[(c[0], c[2]) for c in columnas])
    for item in items:
        tabla.add_row(*[_celda(funcion(item)) for _, funcion, _ in columnas])
    return tabla


def mostrar(items: Iterable[object], vacio: str) -> None:
    """Muestra una lista de objetos como tabla.

    Args:
        items (Iterable[object]): Objetos a mostrar.
        vacio (str): Mensaje si no hay registros.
    """
    items = list(items)
    if not items:
        consola.print(f"  [suave]{escape(vacio)}[/]")
        return
    tabla = tabla_de(items)
    if tabla is None:
        for item in items:
            consola.print(f"  {escape(str(item))}")
    else:
        consola.print(tabla)
        consola.print(f"  [suave]{len(items)} registro(s)[/]")


def menu(titulo: str, opciones: List[str], salir: str) -> None:
    """Dibuja un menú dentro de un panel.

    Args:
        titulo (str): Título del menú (con "›" para la ruta).
        opciones (List[str]): Textos de las opciones 1..N.
        salir (str): Texto de la opción 0.
    """
    grilla = Table.grid(padding=(0, 2))
    grilla.add_column(justify="right")
    grilla.add_column()
    for numero, texto in enumerate(opciones, start=1):
        grilla.add_row(f"[numero]{numero}[/]", escape(texto))
    grilla.add_row("[suave]0[/]", f"[suave]{escape(salir)}[/]")
    *ruta, actual = titulo.split(" › ")
    encabezado = "".join(f"[suave]{escape(r)} › [/]" for r in ruta)
    consola.print()
    consola.print(Panel(
        grilla, title=f"{encabezado}[titulo]{escape(actual)}[/]",
        title_align="left", border_style="acento", box=box.ROUNDED,
        padding=(1, 2), expand=False,
    ))


def banner(titulo: str, subtitulo: str) -> None:
    """Muestra la portada del sistema."""
    consola.print(Panel(
        f"[titulo]{escape(titulo)}[/]\n[suave]{escape(subtitulo)}[/]",
        border_style="acento", box=box.DOUBLE, padding=(1, 4),
        expand=False,
    ))


# Un valor por defecto se escribe al final del mensaje entre corchetes,
# por ejemplo "Título [Rayuela]". Se muestra atenuado.
_POR_DEFECTO = re.compile(r"^(.*?)\s\[([^\]]*)\](.*)$")


def preguntar(mensaje: str) -> str:
    """Pide un dato al usuario con un estilo uniforme.

    Equivale a input(): funciona igual en terminal y en Colab.

    Args:
        mensaje (str): Texto de la pregunta. Si termina en "[valor]",
            ese valor se muestra como el valor por defecto.

    Returns:
        str: Texto ingresado.
    """
    texto = mensaje.rstrip()
    sufijo = ""
    if texto.endswith(":"):
        texto = texto[:-1]
    coincidencia = _POR_DEFECTO.match(texto)
    if coincidencia:
        texto, valor, resto = coincidencia.groups()
        sufijo = f" [suave](actual: {escape(valor)})[/]{escape(resto)}"
    return consola.input(
        f"  [acento]›[/] {escape(texto.strip())}{sufijo}[acento]:[/] "
    )


def exito(mensaje: str) -> None:
    """Mensaje de operación exitosa."""
    consola.print(f"  [ok]✔[/] {escape(mensaje)}")


def error(mensaje: str) -> None:
    """Mensaje de error."""
    consola.print(f"  [error]✖ {escape(mensaje)}[/]")


def aviso(mensaje: str) -> None:
    """Mensaje de advertencia."""
    consola.print(f"  [aviso]⚠ {escape(mensaje)}[/]")


def info(mensaje: str) -> None:
    """Mensaje informativo."""
    consola.print(f"  [info]ℹ {escape(mensaje)}[/]")


def esperando(mensaje: str):
    """Spinner mientras se consulta algo (uso: with esperando(...):)."""
    return consola.status(f"[info]{escape(mensaje)}[/]", spinner="dots")
