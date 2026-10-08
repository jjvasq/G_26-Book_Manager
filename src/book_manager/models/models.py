"""Tablas del sistema definidas con el ORM de SQLAlchemy.

Cada clase representa una tabla. Las entidades del dominio (paquete
`entities`) no dependen de SQLAlchemy: los repositorios convierten entre
modelos y entidades.

Todas las tablas tienen la columna `estado` para el borrado lógico
(1 = activo, 0 = borrado).
"""

from __future__ import annotations

import datetime
from typing import List, Optional

from sqlalchemy import (
    CheckConstraint, Date, Float, ForeignKey, Integer, String,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from book_manager.database.connection import ConexionDB


class Base(DeclarativeBase):
    """Clase base de todos los modelos."""


class ModeloConEstado:
    """Agrega la columna `estado` usada para el borrado lógico."""

    estado: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


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
    codigo: Mapped[str] = mapped_column(String(3), nullable=False, index=True)
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
    isbn: Mapped[str] = mapped_column(String(13), nullable=False, index=True)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    autor: Mapped[str] = mapped_column(String(150), nullable=False)
    anio: Mapped[int] = mapped_column(Integer, nullable=False)
    genero_id: Mapped[int] = mapped_column(
        ForeignKey("generos.id"), nullable=False
    )
    editorial_id: Mapped[int] = mapped_column(
        ForeignKey("editoriales.id"), nullable=False
    )

    genero: Mapped[GeneroModel] = relationship(back_populates="libros")
    editorial: Mapped[EditorialModel] = relationship(back_populates="libros")
    precios: Mapped[List[PrecioModel]] = relationship(back_populates="libro")
    stock: Mapped[Optional[StockModel]] = relationship(
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

    libro: Mapped[LibroModel] = relationship(back_populates="precios")
    moneda: Mapped[MonedaModel] = relationship(back_populates="precios")


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

    libro: Mapped[LibroModel] = relationship(back_populates="stock")


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
        back_populates="cotizaciones"
    )


def crear_tablas(conexion: ConexionDB) -> None:
    """Crea en la base de datos las tablas que todavía no existen.

    Args:
        conexion (ConexionDB): Conexión a la base de datos.
    """
    Base.metadata.create_all(conexion.engine)


def eliminar_tablas(conexion: ConexionDB) -> None:
    """Elimina todas las tablas del sistema (y sus datos).

    Args:
        conexion (ConexionDB): Conexión a la base de datos.
    """
    Base.metadata.drop_all(conexion.engine)
