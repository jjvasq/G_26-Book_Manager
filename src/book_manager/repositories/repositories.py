"""Repositorios de persistencia en la base de datos (SQLAlchemy).

Las clases de repositorio mantienen las mismas interfaces del Sprint 1
(IRepositorio, IRepositorioStock, IRepositorioCotizacionDolar), por lo que
los servicios y la consola no dependen de dónde se guardan los datos.

Cada operación abre su propia transacción con `ConexionDB.transaccion()`
y convierte los modelos ORM en entidades del dominio antes de cerrarla.
"""

from __future__ import annotations

import abc
import datetime
from dataclasses import dataclass
from typing import Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from book_manager.database.connection import ConexionDB
from book_manager.entities.entities import (
    CotizacionDolar,
    Editorial,
    EntidadBase,
    Genero,
    Libro,
    Moneda,
    Precio,
    Stock,
    TipoCotizacion,
)
from book_manager.models.models import (
    Base,
    CotizacionDolarModel,
    EditorialModel,
    GeneroModel,
    LibroModel,
    MonedaModel,
    PrecioModel,
    StockModel,
    TipoCotizacionModel,
)

# Valores de la columna `estado` (borrado lógico).
ACTIVO = 1
BORRADO = 0

T = TypeVar("T", bound=EntidadBase)


class IRepositorio(abc.ABC, Generic[T]):
    """Interfaz para repositorios que manejan entidades con operaciones CRUD
    básicas."""

    @abc.abstractmethod
    def crear(self, entidad: T) -> T:
        """Crea una nueva entidad en el repositorio.

        Args:
            entidad (T): La entidad a crear.

        Returns:
            T: La entidad creada.

        Raises:
            ValueError: Si ya existe una entidad con el mismo ID.
        """
        pass

    @abc.abstractmethod
    def leer_por_id(self, id: int) -> Optional[T]:
        """Lee una entidad del repositorio por su ID.

        Args:
            id (int): El ID de la entidad a leer.

        Returns:
            Optional[T]: La entidad si se encuentra, None en caso contrario.
        """
        pass

    @abc.abstractmethod
    def leer_todos(self) -> List[T]:
        """Lee todas las entidades del repositorio.

        Returns:
            List[T]: Una lista de todas las entidades.
        """
        pass

    @abc.abstractmethod
    def actualizar(self, entidad: T) -> T:
        """Actualiza una entidad existente en el repositorio.

        Args:
            entidad (T): La entidad a actualizar (debe tener un ID existente).

        Returns:
            T: La entidad actualizada.

        Raises:
            ValueError: Si no se encuentra la entidad para actualizar.
        """
        pass

    @abc.abstractmethod
    def eliminar(self, id: int) -> bool:
        """Elimina una entidad del repositorio por su ID.

        Args:
            id (int): El ID de la entidad a eliminar.

        Returns:
            bool: True si la entidad fue eliminada, False si no se encontró.
        """
        pass


class IRepositorioStock(abc.ABC):
    """Interfaz para repositorios del tipo Stock."""

    @abc.abstractmethod
    def crear(self, stock: Stock) -> Stock:
        """Crea un nuevo registro de stock.

        Args:
            stock (Stock): El objeto Stock a crear.

        Returns:
            Stock: El objeto Stock creado.

        Raises:
            ValueError: Si ya existe un registro de stock para el mismo libro.
        """
        pass

    @abc.abstractmethod
    def leer_por_libro(self, libro_id: int) -> Optional['Stock']:
        """Lee un registro de stock por ID de libro.

        Args:
            libro_id (int): El ID del libro asociado al stock.

        Returns:
            Optional[Stock]: El objeto Stock si se encuentra, None en caso
                contrario.
        """
        pass

    @abc.abstractmethod
    def actualizar(self, stock: 'Stock') -> 'Stock':
        """Actualiza un registro de stock existente.

        Args:
            stock (Stock): El objeto Stock a actualizar (debe tener un libro_id
                existente).

        Returns:
            Stock: El objeto Stock actualizado.

        Raises:
            ValueError: Si no se encuentra el stock para actualizar.
        """
        pass

    @abc.abstractmethod
    def eliminar(self, libro_id: int) -> bool:
        """Elimina un registro de stock por ID de libro.

        Args:
            libro_id (int): El ID del libro asociado al stock a eliminar.

        Returns:
            bool: True si el stock fue eliminado, False si no se encontró.
        """
        pass


class IRepositorioCotizacionDolar(abc.ABC):
    """Interfaz para repositorios del tipo RepositorioCotizacionDolar."""

    @abc.abstractmethod
    def crear(self, cotizacion: 'CotizacionDolar') -> 'CotizacionDolar':
        """Crea una nueva cotización de dólar.

        Args:
            cotizacion (CotizacionDolar): El objeto CotizacionDolar a crear.

        Returns:
            CotizacionDolar: El objeto CotizacionDolar creado.

        Raises:
            ValueError: Si ya existe una cotización para el mismo tipo y fecha.
        """
        pass

    @abc.abstractmethod
    def leer_por_tipo_y_fecha(
        self, tipo_id: int, fecha: datetime.date
    ) -> Optional['CotizacionDolar']:
        """Lee una cotización de dólar por tipo y fecha.

        Args:
            tipo_id (int): El ID del tipo de cotización (e.g., 'Oficial',
                'Blue').
            fecha (datetime.date): La fecha de la cotización.

        Returns:
            Optional[CotizacionDolar]: La cotización si se encuentra, None en
                caso contrario.
        """
        pass

    @abc.abstractmethod
    def leer_historico_por_tipo(self, tipo_id: int) -> List['CotizacionDolar']:
        """Lee el histórico de cotizaciones para un tipo específico.

        Args:
            tipo_id (int): El ID del tipo de cotización.

        Returns:
            List[CotizacionDolar]: Una lista de cotizaciones históricas para el
                tipo dado.
        """
        pass

    @abc.abstractmethod
    def actualizar(self, cotizacion: 'CotizacionDolar') -> 'CotizacionDolar':
        """Actualiza una cotización de dólar existente.

        Args:
            cotizacion (CotizacionDolar): El objeto CotizacionDolar a
                actualizar.

        Returns:
            CotizacionDolar: El objeto CotizacionDolar actualizado.
        """
        pass

    @abc.abstractmethod
    def eliminar(self, tipo_id: int, fecha: datetime.date) -> bool:
        """Elimina una cotización de dólar por tipo y fecha.

        Args:
            tipo_id (int): El ID del tipo de cotización.
            fecha (datetime.date): La fecha de la cotización a eliminar.

        Returns:
            bool: True si la cotización fue eliminada, False si no se encontró.
        """
        pass


class ArchivoCSV:
    """Lectura y escritura de filas en un archivo CSV."""

    def __init__(
        self, nombre_archivo: str, campos: List[str], directorio: str
    ) -> None:
        """Constructor.

        Args:
            nombre_archivo (str): Nombre del archivo CSV.
            campos (List[str]): Columnas del archivo.
            directorio (str): Carpeta donde se guardan los CSV.
        """
        self.__ruta: str = directorio.rstrip("/\\") + "/" + nombre_archivo
        self.__campos: List[str] = campos

    @property
    def ruta(self) -> str:
        """Ruta completa del archivo."""
        return self.__ruta

    def leer(self) -> List[Dict[str, str]]:
        """Devuelve todas las filas del archivo (lista vacía si no existe).

        Returns:
            List[Dict[str, str]]: Lista de filas como diccionarios.
        """
        try:
            with open(self.__ruta, "r", encoding="utf-8") as archivo:
                lineas = [linea.rstrip("\r\n") for linea in archivo]
        except FileNotFoundError:
            return []
        if not lineas:
            return []
        encabezado = self._separar(lineas[0])
        return [
            dict(zip(encabezado, self._separar(linea)))
            for linea in lineas[1:]
            if linea
        ]

    def escribir(self, filas: List[Dict[str, object]]) -> None:
        """Sobrescribe el archivo con las filas indicadas.

        Args:
            filas (List[Dict[str, object]]): Filas a escribir.
        """
        with open(self.__ruta, "w", encoding="utf-8") as archivo:
            archivo.write(self._unir(self.__campos) + "\n")
            for fila in filas:
                valores = [fila[campo] for campo in self.__campos]
                archivo.write(self._unir(valores) + "\n")

    @staticmethod
    def _unir(valores: List[object]) -> str:
        """Arma una línea de CSV con los valores separados por comas.

        Los valores que contienen comas o comillas se encierran entre
        comillas, y las comillas internas se duplican.

        Args:
            valores (List[object]): Valores de la línea.

        Returns:
            str: La línea de CSV.
        """
        campos = []
        for valor in valores:
            texto = str(valor)
            if "," in texto or '"' in texto:
                texto = '"' + texto.replace('"', '""') + '"'
            campos.append(texto)
        return ",".join(campos)

    @staticmethod
    def _separar(linea: str) -> List[str]:
        """Separa una línea de CSV en sus valores.

        Respeta las comas que están dentro de valores entre comillas.

        Args:
            linea (str): Línea leída del archivo.

        Returns:
            List[str]: Los valores de la línea.
        """
        campos = []
        actual = ""
        entre_comillas = False
        i = 0
        while i < len(linea):
            caracter = linea[i]
            if entre_comillas:
                if caracter == '"' and linea[i + 1:i + 2] == '"':
                    actual += '"'
                    i += 1
                elif caracter == '"':
                    entre_comillas = False
                else:
                    actual += caracter
            elif caracter == '"':
                entre_comillas = True
            elif caracter == ",":
                campos.append(actual)
                actual = ""
            else:
                actual += caracter
            i += 1
        campos.append(actual)
        return campos


def _genero(modelo: GeneroModel) -> Genero:
    """Convierte un modelo de género en entidad.

    Args:
        modelo (GeneroModel): Registro de la tabla generos.

    Returns:
        Genero: La entidad obtenida.
    """
    return Genero(modelo.id, modelo.nombre, modelo.descripcion)


def _editorial(modelo: EditorialModel) -> Editorial:
    """Convierte un modelo de editorial en entidad.

    Args:
        modelo (EditorialModel): Registro de la tabla editoriales.

    Returns:
        Editorial: La entidad obtenida.
    """
    return Editorial(modelo.id, modelo.nombre, modelo.pais, modelo.email)


def _moneda(modelo: MonedaModel) -> Moneda:
    """Convierte un modelo de moneda en entidad.

    Args:
        modelo (MonedaModel): Registro de la tabla monedas.

    Returns:
        Moneda: La entidad obtenida.
    """
    return Moneda(
        modelo.id, modelo.codigo, modelo.nombre, modelo.simbolo,
        modelo.equivalencia_usd,
    )


def _tipo(modelo: TipoCotizacionModel) -> TipoCotizacion:
    """Convierte un modelo de tipo de cotización en entidad.

    Args:
        modelo (TipoCotizacionModel): Registro de la tabla tipos_cotizacion.

    Returns:
        TipoCotizacion: La entidad obtenida.
    """
    return TipoCotizacion(modelo.id, modelo.nombre, modelo.descripcion)


def _libro(modelo: LibroModel) -> Libro:
    """Convierte un modelo de libro en entidad, con género y editorial.

    Args:
        modelo (LibroModel): Registro de la tabla libros.

    Returns:
        Libro: La entidad obtenida.
    """
    return Libro(
        modelo.id, modelo.isbn, modelo.titulo, modelo.autor, modelo.anio,
        _genero(modelo.genero), _editorial(modelo.editorial),
    )


def _precio(modelo: PrecioModel) -> Precio:
    """Convierte un modelo de precio en entidad, con libro y moneda.

    Args:
        modelo (PrecioModel): Registro de la tabla precios.

    Returns:
        Precio: La entidad obtenida.
    """
    return Precio(
        modelo.id, _libro(modelo.libro), _moneda(modelo.moneda),
        modelo.monto,
    )


def _stock(modelo: StockModel) -> Stock:
    """Convierte un modelo de stock en entidad, con su libro.

    Args:
        modelo (StockModel): Registro de la tabla stock.

    Returns:
        Stock: La entidad obtenida.
    """
    return Stock(_libro(modelo.libro), modelo.cantidad, modelo.stock_minimo)


def _cotizacion(modelo: CotizacionDolarModel) -> CotizacionDolar:
    """Convierte un modelo de cotización en entidad, con su tipo.

    Args:
        modelo (CotizacionDolarModel): Registro de cotizaciones_dolar.

    Returns:
        CotizacionDolar: La entidad obtenida.
    """
    return CotizacionDolar(
        _tipo(modelo.tipo), modelo.fecha, modelo.compra, modelo.venta
    )


class RepositorioSQL(IRepositorio[T]):
    """Implementación genérica de IRepositorio sobre la base de datos.

    Las subclases indican el modelo (tabla) y cómo convertir entre
    modelo y entidad. El borrado es lógico: se pone `estado` en 0 y las
    lecturas solo devuelven los registros activos.
    """

    MODELO: Type[Base]

    def __init__(self, conexion: ConexionDB) -> None:
        """Constructor.

        Args:
            conexion (ConexionDB): Conexión a la base de datos.
        """
        self._conexion: ConexionDB = conexion

    def _consulta_activos(self) -> Select:
        """Arma la consulta de los registros activos ordenados por ID.

        Returns:
            Select: Consulta de SQLAlchemy.
        """
        return (
            select(self.MODELO)
            .where(self.MODELO.estado == ACTIVO)
            .order_by(self.MODELO.id)
        )

    def _modelo_activo(self, sesion: Session, id: int) -> Optional[Base]:
        """Busca el registro activo con ese ID dentro de una sesión.

        Args:
            sesion (Session): Sesión abierta.
            id (int): ID del registro.

        Returns:
            Optional[Base]: El modelo si existe y está activo.
        """
        modelo = sesion.get(self.MODELO, id)
        if modelo is None or modelo.estado != ACTIVO:
            return None
        return modelo

    def crear(self, entidad: T) -> T:
        """Crea un nuevo registro en la base de datos.

        Si la entidad tiene ID 0, la base asigna el próximo ID.

        Args:
            entidad (T): Entidad a procesar.

        Returns:
            T: La entidad creada, con su ID.

        Raises:
            ValueError: Si ya existe un registro con el mismo ID (aunque
                esté borrado).
        """
        with self._conexion.transaccion() as sesion:
            if entidad.id and sesion.get(self.MODELO, entidad.id):
                raise ValueError(
                    f"Ya existe una entidad con ID {entidad.id}."
                )
            modelo = self.MODELO(estado=ACTIVO)
            if entidad.id:
                modelo.id = entidad.id
            self._copiar(entidad, modelo)
            sesion.add(modelo)
            sesion.flush()
            entidad.id = modelo.id
        return entidad

    def leer_por_id(self, id: int) -> Optional[T]:
        """Lee una entidad activa por su ID.

        Args:
            id (int): ID del registro.

        Returns:
            Optional[T]: La entidad si existe y está activa, None en caso
                contrario.
        """
        with self._conexion.transaccion() as sesion:
            modelo = self._modelo_activo(sesion, id)
            return None if modelo is None else self._a_entidad(modelo)

    def leer_todos(self) -> List[T]:
        """Lee todas las entidades activas ordenadas por ID.

        Returns:
            List[T]: Lista de las entidades activas.
        """
        with self._conexion.transaccion() as sesion:
            return [
                self._a_entidad(modelo)
                for modelo in sesion.scalars(self._consulta_activos())
            ]

    def actualizar(self, entidad: T) -> T:
        """Actualiza el registro con los datos de `entidad`.

        Args:
            entidad (T): Entidad a procesar.

        Returns:
            T: La entidad actualizada.

        Raises:
            ValueError: Si no existe un registro activo con ese ID.
        """
        with self._conexion.transaccion() as sesion:
            modelo = self._modelo_activo(sesion, entidad.id)
            if modelo is None:
                raise ValueError(
                    f"No existe una entidad con ID {entidad.id}."
                )
            self._copiar(entidad, modelo)
        return entidad

    def eliminar(self, id: int) -> bool:
        """Borra lógicamente un registro (estado = 0).

        Args:
            id (int): ID del registro.

        Returns:
            bool: True si se borró, False si no existía o ya estaba
                borrado.
        """
        with self._conexion.transaccion() as sesion:
            modelo = self._modelo_activo(sesion, id)
            if modelo is None:
                return False
            modelo.estado = BORRADO
        return True

    @abc.abstractmethod
    def _a_entidad(self, modelo: Base) -> T:
        """Convierte un registro de la tabla en entidad.

        Args:
            modelo (Base): Registro leído de la base.

        Returns:
            T: La entidad obtenida.
        """

    @abc.abstractmethod
    def _copiar(self, entidad: T, modelo: Base) -> None:
        """Copia los datos de la entidad en el registro de la tabla.

        Args:
            entidad (T): Entidad con los datos.
            modelo (Base): Registro que se modifica.
        """


class RepositorioGenero(RepositorioSQL[Genero]):
    """Repositorio de géneros (tabla generos)."""

    MODELO = GeneroModel

    def _a_entidad(self, modelo: GeneroModel) -> Genero:
        """Convierte el registro en entidad.

        Args:
            modelo (GeneroModel): Registro de la tabla.

        Returns:
            Genero: La entidad obtenida.
        """
        return _genero(modelo)

    def _copiar(self, entidad: Genero, modelo: GeneroModel) -> None:
        """Copia los datos de la entidad en el registro.

        Args:
            entidad (Genero): Entidad con los datos.
            modelo (GeneroModel): Registro que se modifica.
        """
        modelo.nombre = entidad.nombre
        modelo.descripcion = entidad.descripcion


class RepositorioEditorial(RepositorioSQL[Editorial]):
    """Repositorio de editoriales (tabla editoriales)."""

    MODELO = EditorialModel

    def _a_entidad(self, modelo: EditorialModel) -> Editorial:
        """Convierte el registro en entidad.

        Args:
            modelo (EditorialModel): Registro de la tabla.

        Returns:
            Editorial: La entidad obtenida.
        """
        return _editorial(modelo)

    def _copiar(self, entidad: Editorial, modelo: EditorialModel) -> None:
        """Copia los datos de la entidad en el registro.

        Args:
            entidad (Editorial): Entidad con los datos.
            modelo (EditorialModel): Registro que se modifica.
        """
        modelo.nombre = entidad.nombre
        modelo.pais = entidad.pais
        modelo.email = entidad.email


class RepositorioMoneda(RepositorioSQL[Moneda]):
    """Repositorio de monedas (tabla monedas)."""

    MODELO = MonedaModel

    def _a_entidad(self, modelo: MonedaModel) -> Moneda:
        """Convierte el registro en entidad.

        Args:
            modelo (MonedaModel): Registro de la tabla.

        Returns:
            Moneda: La entidad obtenida.
        """
        return _moneda(modelo)

    def _copiar(self, entidad: Moneda, modelo: MonedaModel) -> None:
        """Copia los datos de la entidad en el registro.

        Args:
            entidad (Moneda): Entidad con los datos.
            modelo (MonedaModel): Registro que se modifica.
        """
        modelo.codigo = entidad.codigo
        modelo.nombre = entidad.nombre
        modelo.simbolo = entidad.simbolo
        modelo.equivalencia_usd = entidad.equivalencia_usd


class RepositorioTipoCotizacion(RepositorioSQL[TipoCotizacion]):
    """Repositorio de tipos de cotización (tabla tipos_cotizacion)."""

    MODELO = TipoCotizacionModel

    def _a_entidad(self, modelo: TipoCotizacionModel) -> TipoCotizacion:
        """Convierte el registro en entidad.

        Args:
            modelo (TipoCotizacionModel): Registro de la tabla.

        Returns:
            TipoCotizacion: La entidad obtenida.
        """
        return _tipo(modelo)

    def _copiar(
        self, entidad: TipoCotizacion, modelo: TipoCotizacionModel
    ) -> None:
        """Copia los datos de la entidad en el registro.

        Args:
            entidad (TipoCotizacion): Entidad con los datos.
            modelo (TipoCotizacionModel): Registro que se modifica.
        """
        modelo.nombre = entidad.nombre
        modelo.descripcion = entidad.descripcion


class RepositorioLibro(RepositorioSQL[Libro]):
    """Repositorio de libros (tabla libros)."""

    MODELO = LibroModel

    def leer_por_isbn(self, isbn: str) -> Optional[Libro]:
        """Busca un libro activo por ISBN (con o sin guiones).

        Args:
            isbn (str): ISBN de 10 o 13 caracteres.

        Returns:
            Optional[Libro]: El libro si existe, None en caso contrario.
        """
        isbn = isbn.replace("-", "").replace(" ", "").upper()
        with self._conexion.transaccion() as sesion:
            modelo = sesion.scalars(
                self._consulta_activos().where(LibroModel.isbn == isbn)
            ).first()
            return None if modelo is None else _libro(modelo)

    def _a_entidad(self, modelo: LibroModel) -> Libro:
        """Convierte el registro en entidad.

        Args:
            modelo (LibroModel): Registro de la tabla.

        Returns:
            Libro: La entidad obtenida.
        """
        return _libro(modelo)

    def _copiar(self, entidad: Libro, modelo: LibroModel) -> None:
        """Copia los datos de la entidad en el registro.

        Args:
            entidad (Libro): Entidad con los datos.
            modelo (LibroModel): Registro que se modifica.
        """
        modelo.isbn = entidad.isbn
        modelo.titulo = entidad.titulo
        modelo.autor = entidad.autor
        modelo.anio = entidad.anio
        modelo.genero_id = entidad.genero.id
        modelo.editorial_id = entidad.editorial.id


class RepositorioPrecio(RepositorioSQL[Precio]):
    """Repositorio de precios (tabla precios)."""

    MODELO = PrecioModel

    def leer_por_libro(self, libro_id: int) -> List[Precio]:
        """Devuelve los precios activos de un libro.

        Args:
            libro_id (int): ID del libro.

        Returns:
            List[Precio]: Lista de precios del libro.
        """
        with self._conexion.transaccion() as sesion:
            return [
                _precio(modelo) for modelo in sesion.scalars(
                    self._consulta_activos()
                    .where(PrecioModel.libro_id == libro_id)
                )
            ]

    def leer_por_moneda(self, moneda_id: int) -> List[Precio]:
        """Devuelve los precios activos expresados en una moneda.

        Args:
            moneda_id (int): ID de la moneda.

        Returns:
            List[Precio]: Lista de precios en esa moneda.
        """
        with self._conexion.transaccion() as sesion:
            return [
                _precio(modelo) for modelo in sesion.scalars(
                    self._consulta_activos()
                    .where(PrecioModel.moneda_id == moneda_id)
                )
            ]

    def _a_entidad(self, modelo: PrecioModel) -> Precio:
        """Convierte el registro en entidad.

        Args:
            modelo (PrecioModel): Registro de la tabla.

        Returns:
            Precio: La entidad obtenida.
        """
        return _precio(modelo)

    def _copiar(self, entidad: Precio, modelo: PrecioModel) -> None:
        """Copia los datos de la entidad en el registro.

        Args:
            entidad (Precio): Entidad con los datos.
            modelo (PrecioModel): Registro que se modifica.
        """
        modelo.libro_id = entidad.libro.id
        modelo.moneda_id = entidad.moneda.id
        modelo.monto = entidad.monto


class RepositorioStock(IRepositorioStock):
    """Repositorio de stock (tabla stock), identificado por el libro."""

    def __init__(self, conexion: ConexionDB) -> None:
        """Constructor.

        Args:
            conexion (ConexionDB): Conexión a la base de datos.
        """
        self.__conexion: ConexionDB = conexion

    @staticmethod
    def _activo(sesion: Session, libro_id: int) -> Optional[StockModel]:
        """Busca el stock activo de un libro dentro de una sesión.

        Args:
            sesion (Session): Sesión abierta.
            libro_id (int): ID del libro.

        Returns:
            Optional[StockModel]: El registro si existe y está activo.
        """
        modelo = sesion.get(StockModel, libro_id)
        if modelo is None or modelo.estado != ACTIVO:
            return None
        return modelo

    def crear(self, stock: Stock) -> Stock:
        """Crea un nuevo registro en la base de datos.

        Si había un registro borrado para ese libro, se reactiva con los
        datos nuevos.

        Args:
            stock (Stock): Stock del libro.

        Returns:
            Stock: La entidad creada.

        Raises:
            ValueError: Si el libro ya tiene stock activo.
        """
        with self.__conexion.transaccion() as sesion:
            modelo = sesion.get(StockModel, stock.libro_id)
            if modelo is not None and modelo.estado == ACTIVO:
                raise ValueError("El libro ya tiene stock registrado.")
            if modelo is None:
                modelo = StockModel(libro_id=stock.libro_id)
                sesion.add(modelo)
            modelo.cantidad = stock.cantidad
            modelo.stock_minimo = stock.stock_minimo
            modelo.estado = ACTIVO
        return stock

    def leer_por_libro(self, libro_id: int) -> Optional[Stock]:
        """Lee el stock activo de un libro.

        Args:
            libro_id (int): ID del libro.

        Returns:
            Optional[Stock]: El stock si existe y está activo.
        """
        with self.__conexion.transaccion() as sesion:
            modelo = self._activo(sesion, libro_id)
            return None if modelo is None else _stock(modelo)

    def leer_todos(self) -> List[Stock]:
        """Devuelve los registros de stock activos ordenados por libro.

        Returns:
            List[Stock]: Lista de registros.
        """
        with self.__conexion.transaccion() as sesion:
            return [
                _stock(modelo) for modelo in sesion.scalars(
                    select(StockModel)
                    .where(StockModel.estado == ACTIVO)
                    .order_by(StockModel.libro_id)
                )
            ]

    def actualizar(self, stock: Stock) -> Stock:
        """Actualiza un registro existente.

        Args:
            stock (Stock): Stock del libro.

        Returns:
            Stock: La entidad actualizada.

        Raises:
            ValueError: Si el libro no tiene stock activo.
        """
        with self.__conexion.transaccion() as sesion:
            modelo = self._activo(sesion, stock.libro_id)
            if modelo is None:
                raise ValueError("El libro no tiene stock registrado.")
            modelo.cantidad = stock.cantidad
            modelo.stock_minimo = stock.stock_minimo
        return stock

    def eliminar(self, libro_id: int) -> bool:
        """Borra lógicamente un registro (estado = 0).

        Args:
            libro_id (int): ID del libro.

        Returns:
            bool: True si se borró, False si no existía o ya estaba
                borrado.
        """
        with self.__conexion.transaccion() as sesion:
            modelo = self._activo(sesion, libro_id)
            if modelo is None:
                return False
            modelo.estado = BORRADO
        return True


class RepositorioCotizacionDolar(IRepositorioCotizacionDolar):
    """Repositorio de cotizaciones (tabla cotizaciones_dolar).

    Cada cotización se identifica por tipo y fecha (clave compuesta).
    """

    def __init__(self, conexion: ConexionDB) -> None:
        """Constructor.

        Args:
            conexion (ConexionDB): Conexión a la base de datos.
        """
        self.__conexion: ConexionDB = conexion

    @staticmethod
    def _activa(
        sesion: Session, tipo_id: int, fecha: datetime.date
    ) -> Optional[CotizacionDolarModel]:
        """Busca la cotización activa de un tipo y fecha.

        Args:
            sesion (Session): Sesión abierta.
            tipo_id (int): ID del tipo de cotización.
            fecha (datetime.date): Fecha de la cotización.

        Returns:
            Optional[CotizacionDolarModel]: El registro si existe y está
                activo.
        """
        modelo = sesion.get(CotizacionDolarModel, (tipo_id, fecha))
        if modelo is None or modelo.estado != ACTIVO:
            return None
        return modelo

    def _listar(self, tipo_id: Optional[int] = None) -> List[CotizacionDolar]:
        """Lee las cotizaciones activas ordenadas por fecha y tipo.

        Args:
            tipo_id (Optional[int]): Si se indica, solo las de ese tipo.

        Returns:
            List[CotizacionDolar]: Cotizaciones encontradas.
        """
        consulta = (
            select(CotizacionDolarModel)
            .where(CotizacionDolarModel.estado == ACTIVO)
            .order_by(CotizacionDolarModel.fecha, CotizacionDolarModel.tipo_id)
        )
        if tipo_id is not None:
            consulta = consulta.where(CotizacionDolarModel.tipo_id == tipo_id)
        with self.__conexion.transaccion() as sesion:
            return [_cotizacion(m) for m in sesion.scalars(consulta)]

    def crear(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Crea un nuevo registro en la base de datos.

        Si había una cotización borrada para ese tipo y fecha, se reactiva
        con los datos nuevos.

        Args:
            cotizacion (CotizacionDolar): Cotización del dólar.

        Returns:
            CotizacionDolar: La entidad creada.

        Raises:
            ValueError: Si ya existe una cotización activa para ese tipo y
                fecha.
        """
        clave = (cotizacion.tipo_id, cotizacion.fecha)
        with self.__conexion.transaccion() as sesion:
            modelo = sesion.get(CotizacionDolarModel, clave)
            if modelo is not None and modelo.estado == ACTIVO:
                raise ValueError(
                    "Ya existe una cotización para ese tipo y fecha."
                )
            if modelo is None:
                modelo = CotizacionDolarModel(
                    tipo_id=cotizacion.tipo_id, fecha=cotizacion.fecha
                )
                sesion.add(modelo)
            modelo.compra = cotizacion.compra
            modelo.venta = cotizacion.venta
            modelo.estado = ACTIVO
        return cotizacion

    def leer_por_tipo_y_fecha(
        self, tipo_id: int, fecha: datetime.date
    ) -> Optional[CotizacionDolar]:
        """Lee una cotización activa por tipo y fecha.

        Args:
            tipo_id (int): ID del tipo de cotización.
            fecha (datetime.date): Fecha de la cotización.

        Returns:
            Optional[CotizacionDolar]: La cotización si existe y está
                activa, None en caso contrario.
        """
        with self.__conexion.transaccion() as sesion:
            modelo = self._activa(sesion, tipo_id, fecha)
            return None if modelo is None else _cotizacion(modelo)

    def leer_historico_por_tipo(self, tipo_id: int) -> List[CotizacionDolar]:
        """Lee el histórico de cotizaciones de un tipo.

        Args:
            tipo_id (int): ID del tipo de cotización.

        Returns:
            List[CotizacionDolar]: Cotizaciones del tipo indicado.
        """
        return self._listar(tipo_id)

    def leer_todos(self) -> List[CotizacionDolar]:
        """Devuelve las cotizaciones activas ordenadas por fecha y tipo.

        Returns:
            List[CotizacionDolar]: Cotizaciones ordenadas por fecha y tipo.
        """
        return self._listar()

    def actualizar(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Actualiza un registro existente.

        Args:
            cotizacion (CotizacionDolar): Cotización del dólar.

        Returns:
            CotizacionDolar: La entidad actualizada.

        Raises:
            ValueError: Si no existe la cotización activa.
        """
        with self.__conexion.transaccion() as sesion:
            modelo = self._activa(sesion, cotizacion.tipo_id, cotizacion.fecha)
            if modelo is None:
                raise ValueError(
                    "No existe una cotización para ese tipo y fecha."
                )
            modelo.compra = cotizacion.compra
            modelo.venta = cotizacion.venta
        return cotizacion

    def eliminar(self, tipo_id: int, fecha: datetime.date) -> bool:
        """Borra lógicamente un registro (estado = 0).

        Args:
            tipo_id (int): ID del tipo de cotización.
            fecha (datetime.date): Fecha de la cotización.

        Returns:
            bool: True si se borró, False si no existía o ya estaba
                borrado.
        """
        with self.__conexion.transaccion() as sesion:
            modelo = self._activa(sesion, tipo_id, fecha)
            if modelo is None:
                return False
            modelo.estado = BORRADO
        return True


@dataclass
class Repositorios:
    """Agrupa todos los repositorios del sistema."""

    generos: RepositorioGenero
    editoriales: RepositorioEditorial
    monedas: RepositorioMoneda
    tipos_cotizacion: RepositorioTipoCotizacion
    libros: RepositorioLibro
    precios: RepositorioPrecio
    stock: RepositorioStock
    cotizaciones: RepositorioCotizacionDolar


def crear_repositorios(conexion: Optional[ConexionDB] = None) -> Repositorios:
    """Instancia los repositorios sobre una misma conexión.

    Args:
        conexion (Optional[ConexionDB]): Conexión a la base de datos. Si
            es None se crea una con la configuración del .env.

    Returns:
        Repositorios: Los repositorios del sistema.
    """
    conexion = conexion or ConexionDB()
    return Repositorios(
        generos=RepositorioGenero(conexion),
        editoriales=RepositorioEditorial(conexion),
        monedas=RepositorioMoneda(conexion),
        tipos_cotizacion=RepositorioTipoCotizacion(conexion),
        libros=RepositorioLibro(conexion),
        precios=RepositorioPrecio(conexion),
        stock=RepositorioStock(conexion),
        cotizaciones=RepositorioCotizacionDolar(conexion),
    )
