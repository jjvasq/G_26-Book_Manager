"""Tablas del sistema definidas con el ORM de SQLAlchemy.

Cada clase representa una tabla. Las entidades del dominio (paquete
`entities`) no dependen de SQLAlchemy: los repositorios convierten entre
modelos y entidades.

Todas las tablas tienen la columna `estado` para el borrado lógico
(1 = activo, 0 = borrado). Por eso las reglas de unicidad del dominio
(ISBN, código de moneda, nombres, un precio por libro y moneda) se
implementan con índices únicos parciales que solo alcanzan a los registros
activos: un registro borrado no impide volver a dar de alta el mismo valor.
"""

from __future__ import annotations

import datetime
from typing import List, Optional

from sqlalchemy import (
    CheckConstraint,
    ColumnElement,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.schema import CreateIndex

from book_manager.database.connection import ConexionDB


# Valor de la columna `estado` de los registros activos.
ESTADO_ACTIVO = 1


class Base(DeclarativeBase):
    """Clase base de todos los modelos."""


class ModeloConEstado:
    """Agrega la columna `estado` usada para el borrado lógico."""

    estado: Mapped[int] = mapped_column(
        Integer, nullable=False, default=ESTADO_ACTIVO
    )


class GeneroModel(ModeloConEstado, Base):
    """Tabla de géneros literarios."""

    __tablename__ = "generos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    descripcion: Mapped[str] = mapped_column(
        String(255), nullable=False, default=""
    )

    libros: Mapped[List[LibroModel]] = relationship(back_populates="genero")


class EditorialModel(ModeloConEstado, Base):
    """Tabla de editoriales."""

    __tablename__ = "editoriales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    pais: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(150), nullable=False)

    libros: Mapped[List[LibroModel]] = relationship(
        back_populates="editorial"
    )


class MonedaModel(ModeloConEstado, Base):
    """Tabla de monedas."""

    __tablename__ = "monedas"
    __table_args__ = (
        CheckConstraint("equivalencia_usd > 0", name="ck_moneda_equivalencia"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(3), nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    simbolo: Mapped[str] = mapped_column(String(10), nullable=False)
    equivalencia_usd: Mapped[float] = mapped_column(Float, nullable=False)

    precios: Mapped[List[PrecioModel]] = relationship(back_populates="moneda")


class TipoCotizacionModel(ModeloConEstado, Base):
    """Tabla de tipos de cotización del dólar (Oficial, Blue, MEP...)."""

    __tablename__ = "tipos_cotizacion"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50), nullable=False)
    descripcion: Mapped[str] = mapped_column(
        String(255), nullable=False, default=""
    )

    cotizaciones: Mapped[List[CotizacionDolarModel]] = relationship(
        back_populates="tipo"
    )


class LibroModel(ModeloConEstado, Base):
    """Tabla de libros, referencia a género y editorial."""

    __tablename__ = "libros"
    __table_args__ = (CheckConstraint("anio > 0", name="ck_libro_anio"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    isbn: Mapped[str] = mapped_column(String(13), nullable=False)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    autor: Mapped[str] = mapped_column(String(150), nullable=False)
    anio: Mapped[int] = mapped_column(Integer, nullable=False)
    genero_id: Mapped[int] = mapped_column(
        ForeignKey("generos.id"), nullable=False
    )
    editorial_id: Mapped[int] = mapped_column(
        ForeignKey("editoriales.id"), nullable=False
    )

    genero: Mapped[GeneroModel] = relationship(
        back_populates="libros", lazy="joined"
    )
    editorial: Mapped[EditorialModel] = relationship(
        back_populates="libros", lazy="joined"
    )
    precios: Mapped[List[PrecioModel]] = relationship(back_populates="libro")
    stock: Mapped[Optional[StockModel]] = relationship(
        back_populates="libro"
    )
    precios_web: Mapped[List[PrecioWebModel]] = relationship(
        back_populates="libro"
    )


class PrecioModel(ModeloConEstado, Base):
    """Tabla de precios: monto de un libro en una moneda."""

    __tablename__ = "precios"
    __table_args__ = (CheckConstraint("monto > 0", name="ck_precio_monto"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    libro_id: Mapped[int] = mapped_column(
        ForeignKey("libros.id"), nullable=False
    )
    moneda_id: Mapped[int] = mapped_column(
        ForeignKey("monedas.id"), nullable=False
    )
    monto: Mapped[float] = mapped_column(Float, nullable=False)

    libro: Mapped[LibroModel] = relationship(
        back_populates="precios", lazy="joined"
    )
    moneda: Mapped[MonedaModel] = relationship(
        back_populates="precios", lazy="joined"
    )


class StockModel(ModeloConEstado, Base):
    """Tabla de stock. La clave primaria es el ID del libro (1 a 1)."""

    __tablename__ = "stock"
    __table_args__ = (
        CheckConstraint("cantidad >= 0", name="ck_stock_cantidad"),
        CheckConstraint("stock_minimo >= 0", name="ck_stock_minimo"),
    )

    libro_id: Mapped[int] = mapped_column(
        ForeignKey("libros.id"), primary_key=True
    )
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    stock_minimo: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    libro: Mapped[LibroModel] = relationship(
        back_populates="stock", lazy="joined"
    )


class CotizacionDolarModel(ModeloConEstado, Base):
    """Tabla de cotizaciones, clave primaria compuesta (tipo, fecha)."""

    __tablename__ = "cotizaciones_dolar"
    __table_args__ = (
        CheckConstraint("compra > 0", name="ck_cotizacion_compra"),
        CheckConstraint("venta > 0", name="ck_cotizacion_venta"),
    )

    tipo_id: Mapped[int] = mapped_column(
        ForeignKey("tipos_cotizacion.id"), primary_key=True
    )
    fecha: Mapped[datetime.date] = mapped_column(Date, primary_key=True)
    compra: Mapped[float] = mapped_column(Float, nullable=False)
    venta: Mapped[float] = mapped_column(Float, nullable=False)

    tipo: Mapped[TipoCotizacionModel] = relationship(
        back_populates="cotizaciones", lazy="joined"
    )


class PrecioWebModel(ModeloConEstado, Base):
    """Tabla de precios publicados por la competencia (scraping).

    Cada fila es uno de los resultados de la búsqueda de un libro en el
    sitio. `ejecucion` agrupa las filas de una misma ejecución del
    scraper y `fecha_extraccion` es el momento en que se leyó la página.
    Las formas de pago se guardan como JSON.
    """

    __tablename__ = "precios_web"
    __table_args__ = (
        CheckConstraint("precio > 0", name="ck_precio_web_precio"),
        CheckConstraint("posicion >= 1", name="ck_precio_web_posicion"),
        CheckConstraint(
            "relevancia >= 0 AND relevancia <= 1",
            name="ck_precio_web_relevancia",
        ),
        Index("ix_precios_web_libro_ejecucion", "libro_id", "ejecucion"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    libro_id: Mapped[int] = mapped_column(
        ForeignKey("libros.id"), nullable=False
    )
    sitio: Mapped[str] = mapped_column(String(50), nullable=False)
    ejecucion: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False
    )
    fecha_extraccion: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False
    )
    posicion: Mapped[int] = mapped_column(Integer, nullable=False)
    titulo: Mapped[str] = mapped_column(String(300), nullable=False)
    autor: Mapped[str] = mapped_column(
        String(200), nullable=False, default=""
    )
    isbn: Mapped[str] = mapped_column(String(13), nullable=False, default="")
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    url_imagen: Mapped[str] = mapped_column(
        String(500), nullable=False, default=""
    )
    precio: Mapped[float] = mapped_column(Float, nullable=False)
    precio_usd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    formas_pago: Mapped[str] = mapped_column(
        Text, nullable=False, default="[]"
    )
    descripcion: Mapped[str] = mapped_column(
        Text, nullable=False, default=""
    )
    relevancia: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )

    libro: Mapped[LibroModel] = relationship(
        back_populates="precios_web", lazy="joined"
    )


class AuditoriaModel(ModeloConEstado, Base):
    """Tabla de auditoría: una fila por cada operación del sistema."""

    __tablename__ = "auditoria"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    accion: Mapped[str] = mapped_column(String(100), nullable=False)
    fecha: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, index=True
    )
    detalles: Mapped[str] = mapped_column(Text, nullable=False, default="")


def _indice_unico_activos(
    nombre: str, estado: Mapped[int], *expresiones: ColumnElement
) -> Index:
    """Crea un índice único parcial sobre los registros activos.

    Args:
        nombre (str): Nombre del índice en la base de datos.
        estado (Mapped[int]): Columna `estado` de la tabla.
        *expresiones (ColumnElement): Columnas o expresiones que no pueden
            repetirse entre los registros activos.

    Returns:
        Index: Índice asociado a la tabla de las columnas.
    """
    condicion = estado == ESTADO_ACTIVO
    return Index(
        nombre,
        *expresiones,
        unique=True,
        postgresql_where=condicion,
        sqlite_where=condicion,
    )


# Unicidad del dominio. Los nombres se comparan sin distinguir mayúsculas,
# igual que en las validaciones de los servicios.
INDICES_UNICOS: List[Index] = [
    _indice_unico_activos(
        "uq_libros_isbn_activo", LibroModel.estado, LibroModel.isbn
    ),
    _indice_unico_activos(
        "uq_monedas_codigo_activo", MonedaModel.estado, MonedaModel.codigo
    ),
    _indice_unico_activos(
        "uq_generos_nombre_activo",
        GeneroModel.estado,
        func.lower(GeneroModel.nombre),
    ),
    _indice_unico_activos(
        "uq_editoriales_nombre_activo",
        EditorialModel.estado,
        func.lower(EditorialModel.nombre),
    ),
    _indice_unico_activos(
        "uq_tipos_cotizacion_nombre_activo",
        TipoCotizacionModel.estado,
        func.lower(TipoCotizacionModel.nombre),
    ),
    _indice_unico_activos(
        "uq_precios_libro_moneda_activo",
        PrecioModel.estado,
        PrecioModel.libro_id,
        PrecioModel.moneda_id,
    ),
]


def crear_tablas(conexion: ConexionDB) -> None:
    """Crea las tablas y los índices únicos que todavía no existen.

    `create_all` no modifica tablas que ya existen, por eso los índices
    únicos se crean también por separado (CREATE UNIQUE INDEX IF NOT
    EXISTS): así una base creada antes de agregarlos los incorpora sin
    perder datos.

    Args:
        conexion (ConexionDB): Conexión a la base de datos.
    """
    Base.metadata.create_all(conexion.engine)
    with conexion.engine.begin() as conexion_db:
        for indice in INDICES_UNICOS:
            conexion_db.execute(CreateIndex(indice, if_not_exists=True))


def eliminar_tablas(conexion: ConexionDB) -> None:
    """Elimina todas las tablas del sistema (y sus datos).

    Args:
        conexion (ConexionDB): Conexión a la base de datos.
    """
    Base.metadata.drop_all(conexion.engine)
