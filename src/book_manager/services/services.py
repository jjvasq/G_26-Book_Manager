"""Servicios con la lógica de negocio de Book Manager."""

from __future__ import annotations

import datetime
import difflib
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
from dataclasses import dataclass
from typing import (
    Any, Callable, Dict, Generic, List, Optional, Tuple, TypeVar,
)
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv

from book_manager.database.connection import ARCHIVO_ENV
from book_manager.entities.entities import (
    CotizacionDolar,
    Editorial,
    EntidadBase,
    FormaPago,
    Genero,
    Libro,
    Moneda,
    Precio,
    PrecioWeb,
    Stock,
    TipoCotizacion,
)
from book_manager.exceptions.exceptions import (
    ApiCotizacionesError,
    ConfiguracionError,
    DatoInvalidoError,
    RegistroDuplicadoError,
    RegistroEnUsoError,
    RegistroNoEncontradoError,
    ScrapingError,
)
from book_manager.repositories.repositories import (
    ArchivoCSV,
    IRepositorio,
    IRepositorioCotizacionDolar,
    IRepositorioStock,
    RepositorioLibro,
    RepositorioPrecio,
    RepositorioPrecioWeb,
    RepositorioStock,
    Repositorios,
)

T = TypeVar("T", bound=EntidadBase)

# Carpeta src del proyecto, que debe estar en el PYTHONPATH del proceso del
# scraper.
CARPETA_SRC = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

# Sitio de la competencia que recorre el scraper.
SITIO_CUSPIDE = "Cúspide"

# Segundos máximos que puede durar una ejecución del scraper.
SEGUNDOS_MAXIMOS_SCRAPING = 900

# Relevancia mínima para considerar que un resultado de la búsqueda por
# título es el libro del catálogo.
RELEVANCIA_MINIMA = 0.7

# Carpeta donde se guardan las alertas y los reportes de la competencia.
CARPETA_REPORTES = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reportes"
)

# Carpeta donde se guardan los CSV de precios exportados.
CARPETA_EXPORTACION = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "exports"
)

# Variable del archivo .env con la URL de DolarApi.
VARIABLE_API_URL = "API_URL"

# Minutos durante los que una consulta a DolarApi se considera vigente.
MINUTOS_VIGENCIA_COTIZACION = 5

# Identificación que se envía a DolarApi; algunos servidores rechazan el
# agente por defecto de requests.
AGENTE_HTTP = "BookManager/1.0 (+https://dolarapi.com)"

# Zona horaria de las cotizaciones: DolarApi informa la fecha en UTC.
ZONA_HORARIA_COTIZACIONES = ZoneInfo("America/Argentina/Buenos_Aires")

# Longitud máxima del nombre de un tipo de cotización (tabla
# tipos_cotizacion).
LARGO_NOMBRE_TIPO = 50

# Nombre con el que se registra en el sistema cada "casa" de DolarApi. Las
# casas que no figuran aquí se dan de alta con el nombre que informa la API.
CASAS_DOLAR_API: Dict[str, str] = {
    "oficial": "Oficial",
    "blue": "Blue",
    "bolsa": "MEP",
    "contadoconliqui": "CCL",
    "tarjeta": "Tarjeta",
    "mayorista": "Mayorista",
    "cripto": "Cripto",
}


class ServicioCRUD(Generic[T]):
    """Servicio base con operaciones CRUD y validaciones propias."""

    def __init__(self, repositorio: IRepositorio[T]) -> None:
        """Constructor.

        Args:
            repositorio (IRepositorio[T]): Repositorio principal del
                servicio.
        """
        self.__repositorio: IRepositorio[T] = repositorio

    def listar(self) -> List[T]:
        """Devuelve todas las entidades.

        Returns:
            List[T]: Lista de registros.
        """
        return self.__repositorio.leer_todos()

    def obtener(self, id: int) -> T:
        """Devuelve la entidad con el ID indicado.

        Args:
            id (int): ID del registro.

        Returns:
            T: El registro encontrado.

        Raises:
            RegistroNoEncontradoError: Si no existe.
        """
        entidad = self.__repositorio.leer_por_id(id)
        if entidad is None:
            raise RegistroNoEncontradoError(
                f"No existe un registro con ID {id}."
            )
        return entidad

    def crear(self, entidad: T) -> T:
        """Valida y da de alta una entidad.

        Args:
            entidad (T): Entidad a procesar.

        Returns:
            T: La entidad creada.
        """
        self._validar(entidad)
        return self.__repositorio.crear(entidad)

    def actualizar(self, entidad: T) -> T:
        """Valida y actualiza una entidad existente.

        Args:
            entidad (T): Entidad a procesar.

        Returns:
            T: La entidad actualizada.
        """
        self.obtener(entidad.id)
        self._validar(entidad)
        return self.__repositorio.actualizar(entidad)

    def eliminar(self, id: int) -> None:
        """Elimina una entidad si las reglas de negocio lo permiten.

        Args:
            id (int): ID del registro.
        """
        self.obtener(id)
        self._antes_de_eliminar(id)
        self.__repositorio.eliminar(id)

    def _validar(self, entidad: T) -> None:
        """Reglas de validación propias de cada servicio.

        Args:
            entidad (T): Entidad a procesar.
        """

    def _antes_de_eliminar(self, id: int) -> None:
        """Verificaciones o acciones previas a eliminar.

        Args:
            id (int): ID del registro.
        """

    def _verificar_unico(
        self,
        valor: str,
        id: int,
        atributo: Callable[[T], str],
        descripcion: str,
    ) -> None:
        """Verifica que ningún otro registro tenga el mismo valor.

        Args:
            valor (str): Valor a verificar.
            id (int): ID del registro que lo usa (0 si es un alta).
            atributo (Callable[[T], str]): Función (lambda) que devuelve
                el valor a comparar de una entidad.
            descripcion (str): Nombre del atributo para el mensaje de
                error.

        Raises:
            RegistroDuplicadoError: Si otro registro ya tiene ese valor.
        """
        valor = valor.strip().lower()
        for otra in self.__repositorio.leer_todos():
            if otra.id != id and atributo(otra).lower() == valor:
                raise RegistroDuplicadoError(
                    f"Ya existe un registro con ese {descripcion}."
                )


class ServicioGenero(ServicioCRUD[Genero]):
    """Lógica de géneros."""

    def __init__(
        self, repositorio: IRepositorio[Genero], repo_libro: RepositorioLibro
    ) -> None:
        """Constructor.

        Args:
            repositorio (IRepositorio[Genero]): Repositorio
                principal del servicio.
            repo_libro (RepositorioLibro): Repositorio de libros.
        """
        super().__init__(repositorio)
        self.__repo_libro: RepositorioLibro = repo_libro

    def verificar_nombre(self, nombre: str, id: int = 0) -> None:
        """Verifica que ningún otro registro use ese nombre.

        Args:
            nombre (str): Nombre a verificar.
            id (int): ID del registro que lo usa (0 si es un alta).

        Raises:
            RegistroDuplicadoError: Si el nombre ya está en uso.
        """
        self._verificar_unico(nombre, id, lambda e: e.nombre, "nombre")

    def _validar(self, entidad: Genero) -> None:
        """Valida las reglas de negocio antes de guardar.

        Args:
            entidad (Genero): Entidad a procesar.

        Raises:
            ValueError: Si se viola alguna regla de negocio.
        """
        self.verificar_nombre(entidad.nombre, entidad.id)

    def _antes_de_eliminar(self, id: int) -> None:
        """Verifica que el registro se pueda eliminar.

        Args:
            id (int): ID del registro.

        Raises:
            RegistroEnUsoError: Si hay registros que dependen de este.
        """
        if any(
            libro.genero.id == id for libro in self.__repo_libro.leer_todos()
        ):
            raise RegistroEnUsoError(
                "No se puede eliminar: hay libros con ese género."
            )


class ServicioEditorial(ServicioCRUD[Editorial]):
    """Lógica de editoriales."""

    def __init__(
        self,
        repositorio: IRepositorio[Editorial],
        repo_libro: RepositorioLibro,
    ) -> None:
        """Constructor.

        Args:
            repositorio (IRepositorio[Editorial]): Repositorio
                principal del servicio.
            repo_libro (RepositorioLibro): Repositorio de libros.
        """
        super().__init__(repositorio)
        self.__repo_libro: RepositorioLibro = repo_libro

    def verificar_nombre(self, nombre: str, id: int = 0) -> None:
        """Verifica que ningún otro registro use ese nombre.

        Args:
            nombre (str): Nombre a verificar.
            id (int): ID del registro que lo usa (0 si es un alta).

        Raises:
            RegistroDuplicadoError: Si el nombre ya está en uso.
        """
        self._verificar_unico(nombre, id, lambda e: e.nombre, "nombre")

    def _validar(self, entidad: Editorial) -> None:
        """Valida las reglas de negocio antes de guardar.

        Args:
            entidad (Editorial): Entidad a procesar.

        Raises:
            ValueError: Si se viola alguna regla de negocio.
        """
        self.verificar_nombre(entidad.nombre, entidad.id)

    def _antes_de_eliminar(self, id: int) -> None:
        """Verifica que el registro se pueda eliminar.

        Args:
            id (int): ID del registro.

        Raises:
            RegistroEnUsoError: Si hay registros que dependen de este.
        """
        libros = self.__repo_libro.leer_todos()
        if any(libro.editorial.id == id for libro in libros):
            raise RegistroEnUsoError(
                "No se puede eliminar: hay libros de esa editorial."
            )


class ServicioMoneda(ServicioCRUD[Moneda]):
    """Lógica de monedas."""

    def __init__(
        self,
        repositorio: IRepositorio[Moneda],
        repo_precio: RepositorioPrecio,
    ) -> None:
        """Constructor.

        Args:
            repositorio (IRepositorio[Moneda]): Repositorio
                principal del servicio.
            repo_precio (RepositorioPrecio): Repositorio de precios.
        """
        super().__init__(repositorio)
        self.__repo_precio: RepositorioPrecio = repo_precio

    def verificar_codigo(self, codigo: str, id: int = 0) -> None:
        """Verifica que ninguna otra moneda use ese código.

        Args:
            codigo (str): Código a verificar.
            id (int): ID de la moneda que lo usa (0 si es un alta).

        Raises:
            RegistroDuplicadoError: Si el código ya está en uso.
        """
        self._verificar_unico(codigo, id, lambda e: e.codigo, "código")

    def _validar(self, entidad: Moneda) -> None:
        """Valida las reglas de negocio antes de guardar.

        Args:
            entidad (Moneda): Entidad a procesar.

        Raises:
            ValueError: Si se viola alguna regla de negocio.
        """
        self.verificar_codigo(entidad.codigo, entidad.id)

    def _antes_de_eliminar(self, id: int) -> None:
        """Verifica que el registro se pueda eliminar.

        Args:
            id (int): ID del registro.

        Raises:
            RegistroEnUsoError: Si hay registros que dependen de este.
        """
        if self.__repo_precio.leer_por_moneda(id):
            raise RegistroEnUsoError(
                "No se puede eliminar: hay precios en esa moneda."
            )


class ServicioTipoCotizacion(ServicioCRUD[TipoCotizacion]):
    """Lógica de tipos de cotización."""

    def __init__(
        self,
        repositorio: IRepositorio[TipoCotizacion],
        repo_cotizacion: IRepositorioCotizacionDolar,
    ) -> None:
        """Constructor.

        Args:
            repositorio (IRepositorio[TipoCotizacion]): Repositorio
                principal del servicio.
            repo_cotizacion (IRepositorioCotizacionDolar): Repositorio
                de cotizaciones.
        """
        super().__init__(repositorio)
        self.__repo_cotizacion: IRepositorioCotizacionDolar = repo_cotizacion

    def buscar_por_nombre(self, nombre: str) -> Optional[TipoCotizacion]:
        """Busca un tipo por nombre, sin distinguir mayúsculas.

        Args:
            nombre (str): Nombre a buscar.

        Returns:
            Optional[TipoCotizacion]: El tipo si existe, None en caso
                contrario.
        """
        return next(
            (t for t in self.listar() if t.nombre.lower() == nombre.lower()),
            None,
        )

    def verificar_nombre(self, nombre: str, id: int = 0) -> None:
        """Verifica que ningún otro registro use ese nombre.

        Args:
            nombre (str): Nombre a verificar.
            id (int): ID del registro que lo usa (0 si es un alta).

        Raises:
            RegistroDuplicadoError: Si el nombre ya está en uso.
        """
        self._verificar_unico(nombre, id, lambda e: e.nombre, "nombre")

    def _validar(self, entidad: TipoCotizacion) -> None:
        """Valida las reglas de negocio antes de guardar.

        Args:
            entidad (TipoCotizacion): Entidad a procesar.

        Raises:
            ValueError: Si se viola alguna regla de negocio.
        """
        self.verificar_nombre(entidad.nombre, entidad.id)

    def _antes_de_eliminar(self, id: int) -> None:
        """Verifica que el registro se pueda eliminar.

        Args:
            id (int): ID del registro.

        Raises:
            RegistroEnUsoError: Si hay registros que dependen de este.
        """
        if self.__repo_cotizacion.leer_historico_por_tipo(id):
            raise RegistroEnUsoError(
                "No se puede eliminar: hay cotizaciones de ese tipo."
            )


class ServicioLibro(ServicioCRUD[Libro]):
    """Lógica de libros.

    Al eliminar un libro se eliminan sus precios y stock.
    """

    def __init__(
        self,
        repositorio: RepositorioLibro,
        repo_precio: RepositorioPrecio,
        repo_stock: IRepositorioStock,
    ) -> None:
        """Constructor.

        Args:
            repositorio (RepositorioLibro): Repositorio principal del
                servicio.
            repo_precio (RepositorioPrecio): Repositorio de precios.
            repo_stock (IRepositorioStock): Repositorio de stock.
        """
        super().__init__(repositorio)
        self.__repo_libro: RepositorioLibro = repositorio
        self.__repo_precio: RepositorioPrecio = repo_precio
        self.__repo_stock: IRepositorioStock = repo_stock

    def buscar(self, texto: str) -> List[Libro]:
        """Busca libros por título, autor o ISBN.

        Args:
            texto (str): Texto a buscar en título, autor o ISBN.

        Returns:
            List[Libro]: Libros que coinciden con el texto.
        """
        texto = texto.lower().strip()
        return [
            libro for libro in self.listar()
            if texto in libro.titulo.lower()
            or texto in libro.autor.lower()
            or texto in libro.isbn.lower()
        ]

    def verificar_isbn(self, isbn: str, id: int = 0) -> None:
        """Verifica que ningún otro libro use ese ISBN.

        Args:
            isbn (str): ISBN a verificar.
            id (int): ID del libro que lo usa (0 si es un alta).

        Raises:
            RegistroDuplicadoError: Si el ISBN ya lo tiene otro libro.
        """
        existente = self.__repo_libro.leer_por_isbn(isbn)
        if existente is not None and existente.id != id:
            raise RegistroDuplicadoError("Ya existe un libro con ese ISBN.")

    def _validar(self, entidad: Libro) -> None:
        """Valida las reglas de negocio antes de guardar.

        Args:
            entidad (Libro): Entidad a procesar.

        Raises:
            ValueError: Si se viola alguna regla de negocio.
        """
        self.verificar_isbn(entidad.isbn, entidad.id)

    def _antes_de_eliminar(self, id: int) -> None:
        """Elimina en cascada los precios y el stock del libro.

        Args:
            id (int): ID del registro.
        """
        for precio in self.__repo_precio.leer_por_libro(id):
            self.__repo_precio.eliminar(precio.id)
        self.__repo_stock.eliminar(id)


class ServicioPrecio(ServicioCRUD[Precio]):
    """Lógica de precios: un único precio por libro y moneda."""

    def __init__(self, repositorio: RepositorioPrecio) -> None:
        """Constructor.

        Args:
            repositorio (RepositorioPrecio): Repositorio principal del
                servicio.
        """
        super().__init__(repositorio)
        self.__repo_precio: RepositorioPrecio = repositorio

    def listar_por_libro(self, libro_id: int) -> List[Precio]:
        """Devuelve los precios de un libro.

        Args:
            libro_id (int): ID del libro.

        Returns:
            List[Precio]: Lista de precios del libro.
        """
        return self.__repo_precio.leer_por_libro(libro_id)

    def verificar_moneda(
        self, libro_id: int, moneda_id: int, id: int = 0
    ) -> None:
        """Verifica que el libro no tenga otro precio en esa moneda.

        Args:
            libro_id (int): ID del libro.
            moneda_id (int): ID de la moneda.
            id (int): ID del precio (0 si es un alta).

        Raises:
            RegistroDuplicadoError: Si el libro ya tiene un precio en esa
                moneda.
        """
        for otro in self.__repo_precio.leer_por_libro(libro_id):
            if otro.id != id and otro.moneda.id == moneda_id:
                raise RegistroDuplicadoError(
                    "El libro ya tiene un precio en esa moneda; modifíquelo."
                )

    def _validar(self, entidad: Precio) -> None:
        """Valida las reglas de negocio antes de guardar.

        Args:
            entidad (Precio): Entidad a procesar.

        Raises:
            ValueError: Si se viola alguna regla de negocio.
        """
        self.verificar_moneda(entidad.libro.id, entidad.moneda.id, entidad.id)


class ServicioStock:
    """Lógica de stock: altas, movimientos y alertas."""

    def __init__(self, repositorio: RepositorioStock) -> None:
        """Constructor.

        Args:
            repositorio (RepositorioStock): Repositorio de stock.
        """
        self.__repositorio: RepositorioStock = repositorio

    def listar(self) -> List[Stock]:
        """Devuelve todos los registros de stock.

        Returns:
            List[Stock]: Lista de registros.
        """
        return self.__repositorio.leer_todos()

    def obtener(self, libro_id: int) -> Stock:
        """Devuelve el stock de un libro.

        Args:
            libro_id (int): ID del libro.

        Returns:
            Stock: El registro encontrado.

        Raises:
            RegistroNoEncontradoError: Si el libro no tiene stock registrado.
        """
        stock = self.__repositorio.leer_por_libro(libro_id)
        if stock is None:
            raise RegistroNoEncontradoError(
                f"El libro {libro_id} no tiene stock registrado."
            )
        return stock

    def verificar_sin_stock(self, libro_id: int) -> None:
        """Verifica que el libro todavía no tenga stock registrado.

        Args:
            libro_id (int): ID del libro.

        Raises:
            RegistroDuplicadoError: Si el libro ya tiene stock.
        """
        if self.__repositorio.leer_por_libro(libro_id) is not None:
            raise RegistroDuplicadoError(
                f"Ya existe stock para el libro {libro_id}; modifíquelo."
            )

    def crear(self, stock: Stock) -> Stock:
        """Da de alta el stock de un libro.

        Args:
            stock (Stock): Registro de stock.

        Returns:
            Stock: La entidad creada.
        """
        return self.__repositorio.crear(stock)

    def actualizar(self, stock: Stock) -> Stock:
        """Actualiza el stock de un libro.

        Args:
            stock (Stock): Registro de stock.

        Returns:
            Stock: La entidad actualizada.
        """
        return self.__repositorio.actualizar(stock)

    def eliminar(self, libro_id: int) -> None:
        """Elimina el stock de un libro.

        Args:
            libro_id (int): ID del libro.
        """
        self.obtener(libro_id)
        self.__repositorio.eliminar(libro_id)

    def ingresar(self, libro_id: int, unidades: int) -> Stock:
        """Registra el ingreso de unidades de un libro.

        Args:
            libro_id (int): ID del libro.
            unidades (int): Cantidad de unidades.

        Returns:
            Stock: El stock actualizado.
        """
        stock = self.obtener(libro_id)
        stock.ingresar(unidades)
        return self.__repositorio.actualizar(stock)

    def retirar(self, libro_id: int, unidades: int) -> Stock:
        """Registra la salida (venta) de unidades de un libro.

        Args:
            libro_id (int): ID del libro.
            unidades (int): Cantidad de unidades.

        Returns:
            Stock: El stock actualizado.
        """
        stock = self.obtener(libro_id)
        stock.retirar(unidades)
        return self.__repositorio.actualizar(stock)

    def bajo_minimo(self) -> List[Stock]:
        """Devuelve los libros cuyo stock está por debajo del mínimo.

        Returns:
            List[Stock]: Registros con stock por debajo del mínimo.
        """
        return [s for s in self.listar() if s.bajo_minimo]


class ServicioCotizacionDolar:
    """Lógica de cotizaciones del dólar y conversión a pesos."""

    def __init__(
        self,
        repositorio: IRepositorioCotizacionDolar,
        servicio_tipo: ServicioTipoCotizacion,
    ) -> None:
        """Constructor.

        Args:
            repositorio (IRepositorioCotizacionDolar): Repositorio de
                cotizaciones.
            servicio_tipo (ServicioTipoCotizacion): Servicio de tipos de
                cotización.
        """
        self.__repositorio: IRepositorioCotizacionDolar = repositorio
        self.__servicio_tipo: ServicioTipoCotizacion = servicio_tipo
        self.__ultima_consulta: Optional[datetime.datetime] = None
        self.__ultimo_error: Optional[str] = None
        load_dotenv(ARCHIVO_ENV)
        self.__api_url: Optional[str] = os.getenv(VARIABLE_API_URL)

    @property
    def ultima_consulta(self) -> Optional[datetime.datetime]:
        """Momento de la última consulta exitosa a DolarApi."""
        return self.__ultima_consulta

    @property
    def ultimo_error(self) -> Optional[str]:
        """Motivo por el que falló la última consulta a DolarApi."""
        return self.__ultimo_error

    @property
    def api_url(self) -> Optional[str]:
        """URL de DolarApi leída del archivo .env (API_URL)."""
        return self.__api_url

    @property
    def en_tiempo_real(self) -> bool:
        """Indica si las cotizaciones se consultaron hace poco a DolarApi."""
        if self.__ultima_consulta is None:
            return False
        antiguedad = datetime.datetime.now() - self.__ultima_consulta
        return antiguedad < datetime.timedelta(
            minutes=MINUTOS_VIGENCIA_COTIZACION
        )

    def refrescar(self) -> bool:
        """Actualiza las cotizaciones desde DolarApi si no están vigentes.

        Si la API no responde no se lanza error: se siguen usando las
        últimas cotizaciones guardadas.

        Returns:
            bool: True si las cotizaciones están en tiempo real, False
                si no se pudo consultar la API.
        """
        if self.en_tiempo_real:
            return True
        try:
            self.obtener_cotizaciones()
        except (ConfiguracionError, ApiCotizacionesError) as error:
            self.__ultimo_error = str(error)
            return False
        return True

    def listar(self) -> List[CotizacionDolar]:
        """Devuelve todas las cotizaciones.

        Returns:
            List[CotizacionDolar]: Lista de registros.
        """
        return self.__repositorio.leer_todos()

    def historico(self, tipo_id: int) -> List[CotizacionDolar]:
        """Devuelve el histórico de un tipo de cotización.

        Args:
            tipo_id (int): ID del tipo de cotización.

        Returns:
            List[CotizacionDolar]: Cotizaciones del tipo ordenadas por
                fecha.
        """
        self.__servicio_tipo.obtener(tipo_id)
        return self.__repositorio.leer_historico_por_tipo(tipo_id)

    def obtener(self, tipo_id: int, fecha: datetime.date) -> CotizacionDolar:
        """Devuelve la cotización de un tipo en una fecha.

        Args:
            tipo_id (int): ID del tipo de cotización.
            fecha (datetime.date): Fecha de la cotización.

        Returns:
            CotizacionDolar: El registro encontrado.

        Raises:
            RegistroNoEncontradoError: Si no existe.
        """
        cotizacion = self.__repositorio.leer_por_tipo_y_fecha(tipo_id, fecha)
        if cotizacion is None:
            raise RegistroNoEncontradoError(
                "No existe una cotización para ese tipo y fecha."
            )
        return cotizacion

    def ultima(self, tipo_id: int) -> CotizacionDolar:
        """Devuelve la cotización más reciente de un tipo.

        Args:
            tipo_id (int): ID del tipo de cotización.

        Returns:
            CotizacionDolar: La cotización más reciente.

        Raises:
            RegistroNoEncontradoError: Si no hay cotizaciones de ese tipo.
        """
        historico = self.historico(tipo_id)
        if not historico:
            raise RegistroNoEncontradoError(
                "No hay cotizaciones cargadas para ese tipo."
            )
        return max(historico, key=lambda c: c.fecha)

    def crear(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Registra una cotización nueva.

        Args:
            cotizacion (CotizacionDolar): Cotización del dólar.

        Returns:
            CotizacionDolar: La entidad creada.
        """
        self.verificar_fecha(cotizacion.tipo_id, cotizacion.fecha)
        return self.__repositorio.crear(cotizacion)

    def verificar_fecha(self, tipo_id: int, fecha: datetime.date) -> None:
        """Verifica que se pueda cargar una cotización en esa fecha.

        Args:
            tipo_id (int): ID del tipo de cotización.
            fecha (datetime.date): Fecha de la cotización.

        Raises:
            DatoInvalidoError: Si la fecha es futura.
            RegistroDuplicadoError: Si ya hay una cotización de ese tipo en
                esa fecha.
        """
        if fecha > datetime.date.today():
            raise DatoInvalidoError(
                "No se pueden cargar cotizaciones futuras."
            )
        if self.__repositorio.leer_por_tipo_y_fecha(tipo_id, fecha):
            raise RegistroDuplicadoError(
                "Ya existe una cotización de ese tipo en esa fecha."
            )

    def actualizar(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Actualiza los valores de una cotización existente.

        Args:
            cotizacion (CotizacionDolar): Cotización del dólar.

        Returns:
            CotizacionDolar: La entidad actualizada.
        """
        return self.__repositorio.actualizar(cotizacion)

    def eliminar(self, tipo_id: int, fecha: datetime.date) -> None:
        """Elimina una cotización.

        Args:
            tipo_id (int): ID del tipo de cotización.
            fecha (datetime.date): Fecha de la cotización.
        """
        self.obtener(tipo_id, fecha)
        self.__repositorio.eliminar(tipo_id, fecha)

    def obtener_cotizaciones(
        self, timeout: float = 10
    ) -> List[CotizacionDolar]:
        """Busca, descarga y registra en la base las cotizaciones del día.

        La URL se toma de la variable API_URL del archivo .env. Cada casa
        informada por la API se asocia a su tipo de cotización; si el
        tipo todavía no está registrado en el sistema, se da de alta. Si
        ya hay una cotización de ese tipo en la fecha, se actualizan sus
        valores.

        Args:
            timeout (float): Segundos máximos de espera de la API.

        Returns:
            List[CotizacionDolar]: Cotizaciones creadas o actualizadas.

        Raises:
            ConfiguracionError: Si falta API_URL en el archivo .env.
            ApiCotizacionesError: Si no se pudo consultar la API.
        """
        if not self.__api_url:
            raise ConfiguracionError(
                f"Falta la variable {VARIABLE_API_URL} en el archivo .env."
            )
        try:
            respuesta = requests.get(
                self.__api_url,
                timeout=timeout,
                headers={
                    "User-Agent": AGENTE_HTTP,
                    "Accept": "application/json",
                },
            )
            respuesta.raise_for_status()
            datos = respuesta.json()
        except (requests.RequestException, ValueError) as error:
            raise ApiCotizacionesError(
                f"No se pudo consultar la cotización: {error}"
            ) from error

        self.__ultima_consulta = datetime.datetime.now()
        self.__ultimo_error = None
        tipos = {
            tipo.nombre.lower(): tipo
            for tipo in self.__servicio_tipo.listar()
        }
        registradas: List[CotizacionDolar] = []
        for dato in datos:
            casa = str(dato.get("casa") or "").strip()
            venta = dato.get("venta")
            if not casa or not venta:
                continue
            tipo = self.__tipo_de_casa(casa, dato.get("nombre"), tipos)
            compra = dato.get("compra") or venta
            fecha = self._fecha_cotizacion(dato.get("fechaActualizacion"))
            registradas.append(
                CotizacionDolar(tipo, fecha, float(compra), float(venta))
            )
        return self.__repositorio.guardar_varias(registradas)

    def __tipo_de_casa(
        self,
        casa: str,
        nombre_api: Optional[str],
        tipos: Dict[str, TipoCotizacion],
    ) -> TipoCotizacion:
        """Devuelve el tipo de cotización de una casa de DolarApi.

        Si el tipo no está registrado, se da de alta (con las validaciones
        del servicio de tipos) y se agrega al diccionario `tipos`.

        Args:
            casa (str): Identificador de la casa en la API (ej.: "blue").
            nombre_api (Optional[str]): Nombre informado por la API.
            tipos (Dict[str, TipoCotizacion]): Tipos registrados, por
                nombre en minúsculas.

        Returns:
            TipoCotizacion: El tipo existente o el recién creado.
        """
        nombre = (
            CASAS_DOLAR_API.get(casa.lower())
            or str(nombre_api or "").strip()
            or casa.capitalize()
        )[:LARGO_NOMBRE_TIPO]
        tipo = tipos.get(nombre.lower())
        if tipo is None:
            tipo = self.__servicio_tipo.crear(TipoCotizacion(
                0, nombre, f"Alta automática desde DolarApi (casa {casa})"
            ))
            tipos[nombre.lower()] = tipo
        return tipo

    @staticmethod
    def _fecha_cotizacion(texto: Optional[str]) -> datetime.date:
        """Obtiene la fecha local (Argentina) de una cotización de la API.

        Args:
            texto (Optional[str]): Fecha y hora ISO 8601 informada por la
                API (ej.: "2026-10-20T14:58:00.000Z").

        Returns:
            datetime.date: Fecha en la hora de Argentina; si la API no
                informa una fecha válida, la fecha de hoy.
        """
        try:
            momento = datetime.datetime.fromisoformat(
                str(texto or "").replace("Z", "+00:00")
            )
        except ValueError:
            return datetime.datetime.now(ZONA_HORARIA_COTIZACIONES).date()
        if momento.tzinfo is not None:
            momento = momento.astimezone(ZONA_HORARIA_COTIZACIONES)
        return momento.date()

    def registrar_manual(
        self, tipo: TipoCotizacion, compra: float, venta: float
    ) -> CotizacionDolar:
        """Registra la cotización de hoy cargada a mano por el usuario.

        Si ya hay una cotización para ese tipo en el día, se actualiza.

        Args:
            tipo (TipoCotizacion): Tipo de cotización.
            compra (float): Valor de compra.
            venta (float): Valor de venta.

        Returns:
            CotizacionDolar: La cotización creada o actualizada.
        """
        return self.__registrar(
            tipo, datetime.date.today(), compra, venta
        )

    def __registrar(
        self,
        tipo: TipoCotizacion,
        fecha: datetime.date,
        compra: float,
        venta: float,
    ) -> CotizacionDolar:
        """Crea la cotización o actualiza la existente para esa fecha.

        Args:
            tipo (TipoCotizacion): Tipo de cotización.
            fecha (datetime.date): Fecha de la cotización.
            compra (float): Valor de compra.
            venta (float): Valor de venta.

        Returns:
            CotizacionDolar: La cotización creada o actualizada.
        """
        existente = self.__repositorio.leer_por_tipo_y_fecha(tipo.id, fecha)
        if existente is None:
            return self.__repositorio.crear(
                CotizacionDolar(tipo, fecha, compra, venta)
            )
        existente.compra = compra
        existente.venta = venta
        return self.__repositorio.actualizar(existente)

    def convertir_a_pesos(
        self, monto: float, moneda: Moneda, tipo_id: int
    ) -> float:
        """Convierte un monto a pesos con la última cotización del tipo.

        Args:
            monto (float): Importe.
            moneda (Moneda): Moneda del importe.
            tipo_id (int): ID del tipo de cotización.

        Returns:
            float: Importe en pesos.
        """
        if moneda.es_local:
            return monto
        cotizacion = self.ultima(tipo_id)
        return monto * moneda.equivalencia_usd * cotizacion.venta


def normalizar_texto(texto: str) -> str:
    """Pasa un texto a minúsculas, sin tildes ni signos de puntuación.

    Args:
        texto (str): Texto a normalizar.

    Returns:
        str: Texto normalizado, con las palabras separadas por un espacio.
    """
    sin_tildes = unicodedata.normalize("NFKD", texto)
    letras = "".join(
        c.lower() if c.isalnum() else " "
        for c in sin_tildes
        if not unicodedata.combining(c)
    )
    return " ".join(letras.split())


def calcular_relevancia(libro: Libro, titulo: str, autor: str = "") -> float:
    """Calcula cuánto se parece un resultado de la búsqueda al libro.

    La búsqueda en el sitio es por título, y la elección del resultado
    también: se combina el parecido del título (75 %) con la coincidencia
    del autor (25 %).

    Args:
        libro (Libro): Libro del catálogo.
        titulo (str): Título del resultado.
        autor (str): Autor del resultado.

    Returns:
        float: Relevancia entre 0 y 1.
    """
    buscado = normalizar_texto(libro.titulo)
    encontrado = normalizar_texto(titulo)
    parecido = difflib.SequenceMatcher(None, buscado, encontrado).ratio()
    if buscado and f" {buscado} " in f" {encontrado} ":
        parecido = max(parecido, 0.9)
    palabras_autor = {
        palabra for palabra in normalizar_texto(libro.autor).split()
        if len(palabra) > 2
    }
    coincide_autor = bool(
        palabras_autor & set(normalizar_texto(autor).split())
    )
    return round(min(0.75 * parecido + 0.25 * coincide_autor, 1.0), 3)


@dataclass(frozen=True)
class UmbralDiferencia:
    """Diferencia de precio a partir de la cual se genera una alerta.

    Attributes:
        valor (float): Diferencia mínima (mayor a cero).
        porcentual (bool): True si valor es un porcentaje del precio
            interno; False si es un importe en pesos.
    """

    valor: float
    porcentual: bool = True

    def __post_init__(self) -> None:
        """Valida el valor del umbral.

        Raises:
            DatoInvalidoError: Si el valor no es un número mayor a cero.
        """
        if isinstance(self.valor, bool) or not isinstance(
            self.valor, (int, float)
        ) or self.valor <= 0:
            raise DatoInvalidoError(
                "La diferencia de precio debe ser un número mayor a cero."
            )

    @classmethod
    def desde_texto(cls, texto: str) -> UmbralDiferencia:
        """Interpreta la diferencia ingresada por el usuario.

        "10%" es un porcentaje del precio interno; "5000" o "5000,50" es
        un importe en pesos.

        Args:
            texto (str): Diferencia ingresada.

        Returns:
            UmbralDiferencia: El umbral.

        Raises:
            DatoInvalidoError: Si el texto no es un número mayor a cero.
        """
        limpio = texto.strip().replace(" ", "").replace("$", "")
        porcentual = limpio.endswith("%")
        limpio = limpio.rstrip("%")
        if "," in limpio or re.fullmatch(r"\d{1,3}(\.\d{3})+", limpio):
            limpio = limpio.replace(".", "").replace(",", ".")
        try:
            valor = float(limpio)
        except ValueError as error:
            raise DatoInvalidoError(
                "Ingrese un porcentaje (ej.: 10%) o un importe en pesos "
                "(ej.: 5000)."
            ) from error
        return cls(valor, porcentual)

    def supera(self, precio_interno: float, diferencia: float) -> bool:
        """Indica si una diferencia de precio alcanza el umbral.

        Args:
            precio_interno (float): Precio interno en pesos.
            diferencia (float): Precio web menos precio interno.

        Returns:
            bool: True si la diferencia (en valor absoluto) es mayor o
                igual al umbral.
        """
        if self.porcentual:
            return abs(diferencia) / precio_interno * 100 >= self.valor
        return abs(diferencia) >= self.valor

    def __str__(self) -> str:
        """Representacion clara del objeto.

        Returns:
            str: El umbral (ej.: "10 %" o "$ 5,000.00").
        """
        if self.porcentual:
            return f"{self.valor:g} %"
        return f"$ {self.valor:,.2f}"


@dataclass
class ComparacionPrecio:
    """Comparación del precio interno de un libro con el precio web.

    Attributes:
        libro (Libro): Libro del catálogo.
        precio_interno (Optional[float]): Precio interno en pesos (None si
            el libro no tiene precio cargado).
        precio_web (Optional[PrecioWeb]): Resultado de la web que
            corresponde al libro (None si no se encontró).
    """

    libro: Libro
    precio_interno: Optional[float]
    precio_web: Optional[PrecioWeb]

    @property
    def comparable(self) -> bool:
        """Indica si hay precio interno y precio web para comparar."""
        return self.precio_interno is not None and self.precio_web is not None

    @property
    def diferencia(self) -> Optional[float]:
        """Precio web menos precio interno, en pesos."""
        if not self.comparable:
            return None
        return self.precio_web.precio - self.precio_interno

    @property
    def diferencia_porcentual(self) -> Optional[float]:
        """Diferencia como porcentaje del precio interno."""
        if not self.comparable:
            return None
        return self.diferencia / self.precio_interno * 100

    def alerta(self, umbral: UmbralDiferencia) -> str:
        """Describe la alerta de precio, si la diferencia alcanza el umbral.

        Args:
            umbral (UmbralDiferencia): Diferencia que dispara la alerta.

        Returns:
            str: "Competencia más barata", "Competencia más cara" o ""
                si no hay alerta.
        """
        if not self.comparable or not umbral.supera(
            self.precio_interno, self.diferencia
        ):
            return ""
        if self.diferencia < 0:
            return "Competencia más barata"
        return "Competencia más cara"


@dataclass
class ResultadoScraping:
    """Resultado de una ejecución del scraper.

    Attributes:
        ejecucion (datetime.datetime): Inicio de la ejecución.
        precios (List[PrecioWeb]): Precios web registrados.
        comparaciones (List[ComparacionPrecio]): Comparación de cada
            libro del catálogo.
        umbral (UmbralDiferencia): Diferencia ingresada por el usuario.
        archivo_alertas (str): Ruta del CSV de alertas generado.
    """

    ejecucion: datetime.datetime
    precios: List[PrecioWeb]
    comparaciones: List[ComparacionPrecio]
    umbral: UmbralDiferencia
    archivo_alertas: str

    @property
    def alertas(self) -> List[ComparacionPrecio]:
        """Comparaciones cuya diferencia alcanza el umbral."""
        return [c for c in self.comparaciones if c.alerta(self.umbral)]


class ServicioPrecioWeb(ServicioCRUD[PrecioWeb]):
    """Lógica de los precios publicados por la competencia."""

    def __init__(self, repositorio: RepositorioPrecioWeb) -> None:
        """Constructor.

        Args:
            repositorio (RepositorioPrecioWeb): Repositorio principal del
                servicio.
        """
        super().__init__(repositorio)
        self.__repo_web: RepositorioPrecioWeb = repositorio

    def registrar_varios(self, precios: List[PrecioWeb]) -> List[PrecioWeb]:
        """Registra los precios obtenidos en una ejecución del scraper.

        Args:
            precios (List[PrecioWeb]): Precios nuevos.

        Returns:
            List[PrecioWeb]: Los precios registrados, con su ID.
        """
        return self.__repo_web.crear_varios(precios)

    def listar_por_libro(self, libro_id: int) -> List[PrecioWeb]:
        """Devuelve los precios web de un libro (los más recientes primero).

        Args:
            libro_id (int): ID del libro.

        Returns:
            List[PrecioWeb]: Precios web del libro.
        """
        return self.__repo_web.leer_por_libro(libro_id)

    def ultima_ejecucion(self) -> Optional[datetime.datetime]:
        """Devuelve el inicio de la última ejecución del scraper.

        Returns:
            Optional[datetime.datetime]: Inicio de la ejecución, o None
                si nunca se ejecutó.
        """
        return self.__repo_web.leer_ultima_ejecucion()

    def de_ejecucion(
        self, ejecucion: datetime.datetime
    ) -> List[PrecioWeb]:
        """Devuelve los precios obtenidos en una ejecución del scraper.

        Args:
            ejecucion (datetime.datetime): Inicio de la ejecución.

        Returns:
            List[PrecioWeb]: Precios de la ejecución.
        """
        return self.__repo_web.leer_por_ejecucion(ejecucion)


class EjecutorScraper:
    """Ejecuta CuspideSpider en un proceso de Python aparte.

    Scrapy usa Twisted, cuyo reactor no se puede reiniciar dentro de un
    mismo proceso; ejecutarlo aparte permite repetir el scraping desde el
    menú sin reiniciar el notebook.
    """

    def __init__(
        self,
        url_base: Optional[str] = None,
        segundos_maximos: int = SEGUNDOS_MAXIMOS_SCRAPING,
    ) -> None:
        """Constructor.

        Args:
            url_base (Optional[str]): URL del sitio (por defecto Cúspide).
            segundos_maximos (int): Tiempo máximo de la ejecución.
        """
        self.__url_base: Optional[str] = url_base
        self.__segundos_maximos: int = segundos_maximos

    def ejecutar(self, libros: List[Libro]) -> List[Dict[str, Any]]:
        """Busca los libros en el sitio y devuelve los resultados.

        Args:
            libros (List[Libro]): Libros del catálogo a buscar.

        Returns:
            List[Dict[str, Any]]: Un diccionario por resultado, con los
                campos de LibroWebItem.

        Raises:
            ScrapingError: Si el proceso del scraper falla o demora más
                del tiempo máximo.
        """
        with tempfile.TemporaryDirectory(prefix="scraping_") as carpeta:
            catalogo = os.path.join(carpeta, "catalogo.json")
            salida = os.path.join(carpeta, "resultados.jsonl")
            with open(catalogo, "w", encoding="utf-8") as archivo:
                json.dump(
                    [{"id": libro.id, "titulo": libro.titulo}
                     for libro in libros],
                    archivo, ensure_ascii=False,
                )
            comando = [
                sys.executable, "-m", "book_manager.scraper.ejecutar",
                "--catalogo", catalogo, "--salida", salida,
            ]
            if self.__url_base:
                comando += ["--url-base", self.__url_base]
            entorno = dict(os.environ)
            entorno["PYTHONPATH"] = os.pathsep.join(
                filter(None, [CARPETA_SRC, entorno.get("PYTHONPATH")])
            )
            try:
                proceso = subprocess.run(
                    comando, capture_output=True, text=True, env=entorno,
                    timeout=self.__segundos_maximos,
                )
            except subprocess.TimeoutExpired as error:
                raise ScrapingError(
                    "El scraping superó el tiempo máximo de "
                    f"{self.__segundos_maximos} segundos."
                ) from error
            if proceso.returncode != 0:
                ultimas = "\n".join(proceso.stderr.strip().splitlines()[-5:])
                raise ScrapingError(f"Falló el scraper:\n{ultimas}")
            if not os.path.exists(salida):
                return []
            with open(salida, "r", encoding="utf-8") as archivo:
                return [
                    json.loads(linea) for linea in archivo if linea.strip()
                ]


class ServicioCompetencia:
    """Precios de la competencia: scraping, comparación y reportes."""

    def __init__(
        self,
        servicio_libro: ServicioLibro,
        servicio_precio_web: ServicioPrecioWeb,
        servicio_reportes: ServicioReportes,
        servicio_cotizacion: ServicioCotizacionDolar,
        ejecutor: Optional[EjecutorScraper] = None,
    ) -> None:
        """Constructor.

        Args:
            servicio_libro (ServicioLibro): Servicio de libros.
            servicio_precio_web (ServicioPrecioWeb): Servicio de precios
                web.
            servicio_reportes (ServicioReportes): Servicio de reportes,
                para el precio interno en pesos.
            servicio_cotizacion (ServicioCotizacionDolar): Servicio de
                cotizaciones del dólar.
            ejecutor (Optional[EjecutorScraper]): Ejecutor del scraper.
        """
        self.__libros: ServicioLibro = servicio_libro
        self.__precios_web: ServicioPrecioWeb = servicio_precio_web
        self.__reportes: ServicioReportes = servicio_reportes
        self.__cotizaciones: ServicioCotizacionDolar = servicio_cotizacion
        self.__ejecutor: EjecutorScraper = ejecutor or EjecutorScraper()

    @staticmethod
    def _a_precio_web(
        dato: Dict[str, Any], libro: Libro, ejecucion: datetime.datetime
    ) -> PrecioWeb:
        """Convierte un resultado del scraper en un PrecioWeb.

        Args:
            dato (Dict[str, Any]): Resultado del scraper.
            libro (Libro): Libro que se buscó.
            ejecucion (datetime.datetime): Inicio de la ejecución.

        Returns:
            PrecioWeb: El precio web, con su relevancia calculada.
        """
        titulo = dato["titulo"]
        autor = dato.get("autor") or ""
        isbn = dato.get("isbn") or ""
        return PrecioWeb(
            0, libro, SITIO_CUSPIDE, ejecucion,
            datetime.datetime.fromisoformat(dato["fecha_extraccion"]),
            dato["posicion"], titulo, dato["url"], float(dato["precio"]),
            autor, isbn, dato.get("url_imagen") or "",
            dato.get("precio_usd"),
            [FormaPago(**forma) for forma in dato.get("formas_pago") or []],
            dato.get("descripcion") or "",
            calcular_relevancia(libro, titulo, autor),
        )

    def _scrapear(self) -> Tuple[datetime.datetime, List[PrecioWeb]]:
        """Busca en Cúspide los libros del catálogo y guarda los precios.

        Por cada libro se toman los 10 primeros resultados de la búsqueda
        por título; todos se registran en la base con la misma
        `ejecucion`.

        Returns:
            Tuple[datetime.datetime, List[PrecioWeb]]: Inicio de la
                ejecución y precios web registrados.

        Raises:
            ScrapingError: Si falla el scraper.
        """
        ejecucion = datetime.datetime.now().replace(microsecond=0)
        libros = {libro.id: libro for libro in self.__libros.listar()}
        if not libros:
            return ejecucion, []
        resultados = self.__ejecutor.ejecutar(list(libros.values()))
        precios = [
            self._a_precio_web(dato, libros[dato["libro_id"]], ejecucion)
            for dato in resultados
            if dato.get("libro_id") in libros
        ]
        return ejecucion, self.__precios_web.registrar_varios(precios)

    def ejecutar_scraping(
        self,
        umbral: UmbralDiferencia,
        tipo_id: int,
        carpeta: str = CARPETA_REPORTES,
    ) -> ResultadoScraping:
        """Ejecuta el scraper, compara los precios y genera las alertas.

        Cada ejecución genera un archivo CSV de alertas con los libros
        cuya diferencia de precio alcanza el umbral ingresado.

        Args:
            umbral (UmbralDiferencia): Diferencia que dispara una alerta.
            tipo_id (int): Tipo de dólar para pasar a pesos los precios
                internos en moneda extranjera.
            carpeta (str): Carpeta donde se guarda el CSV de alertas.

        Returns:
            ResultadoScraping: Precios obtenidos, comparaciones y ruta del
                archivo de alertas.

        Raises:
            RegistroNoEncontradoError: Si no hay cotizaciones de ese tipo
                de dólar (se verifica antes de ejecutar el scraper).
            ScrapingError: Si falla el scraper.
        """
        self._preparar_cotizacion(tipo_id)
        ejecucion, precios = self._scrapear()
        comparaciones = self.comparar(tipo_id, precios)
        archivo = self.generar_alertas_csv(
            comparaciones, umbral, ejecucion, carpeta
        )
        return ResultadoScraping(
            ejecucion, precios, comparaciones, umbral, archivo
        )

    def _preparar_cotizacion(self, tipo_id: int) -> None:
        """Actualiza las cotizaciones y verifica que haya del tipo elegido.

        Si DolarApi no responde se usa la última cotización guardada.

        Args:
            tipo_id (int): ID del tipo de dólar.

        Raises:
            RegistroNoEncontradoError: Si no hay cotizaciones de ese tipo.
        """
        self.__cotizaciones.refrescar()
        self.__cotizaciones.ultima(tipo_id)

    @staticmethod
    def mejor_resultado(precios: List[PrecioWeb]) -> Optional[PrecioWeb]:
        """Elige, entre los resultados de un libro, el que le corresponde.

        Se toma el de mayor relevancia (a igual relevancia, el que aparece
        primero en la búsqueda), siempre que alcance la relevancia mínima.

        Args:
            precios (List[PrecioWeb]): Resultados de la búsqueda del libro.

        Returns:
            Optional[PrecioWeb]: El resultado elegido, o None si ninguno
                se parece lo suficiente al libro.
        """
        candidatos = [
            precio for precio in precios
            if precio.relevancia >= RELEVANCIA_MINIMA
        ]
        if not candidatos:
            return None
        return max(candidatos, key=lambda p: (p.relevancia, -p.posicion))

    def ultimos_precios(self) -> List[PrecioWeb]:
        """Devuelve los precios de la última ejecución del scraper.

        Returns:
            List[PrecioWeb]: Precios web (vacío si nunca se ejecutó).
        """
        ejecucion = self.__precios_web.ultima_ejecucion()
        if ejecucion is None:
            return []
        return self.__precios_web.de_ejecucion(ejecucion)

    def comparar(
        self, tipo_id: int, precios: Optional[List[PrecioWeb]] = None
    ) -> List[ComparacionPrecio]:
        """Compara el precio interno de cada libro con el precio web.

        Args:
            tipo_id (int): Tipo de dólar para pasar a pesos los precios
                internos en moneda extranjera.
            precios (Optional[List[PrecioWeb]]): Precios web a comparar
                (por defecto, los de la última ejecución del scraper).

        Returns:
            List[ComparacionPrecio]: Una comparación por libro del
                catálogo.
        """
        if precios is None:
            precios = self.ultimos_precios()
        por_libro: Dict[int, List[PrecioWeb]] = {}
        for precio in precios:
            por_libro.setdefault(precio.libro.id, []).append(precio)
        return [
            ComparacionPrecio(
                libro,
                self.__reportes.precio_en_pesos(libro.id, tipo_id),
                self.mejor_resultado(por_libro.get(libro.id, [])),
            )
            for libro in self.__libros.listar()
        ]

    @staticmethod
    def generar_alertas_csv(
        comparaciones: List[ComparacionPrecio],
        umbral: UmbralDiferencia,
        ejecucion: datetime.datetime,
        carpeta: str = CARPETA_REPORTES,
    ) -> str:
        """Genera el archivo CSV de alertas de precio.

        Incluye los libros cuya diferencia con el precio web alcanza el
        umbral (el archivo se genera aunque no haya alertas).

        Args:
            comparaciones (List[ComparacionPrecio]): Comparaciones.
            umbral (UmbralDiferencia): Diferencia que dispara una alerta.
            ejecucion (datetime.datetime): Inicio de la ejecución.
            carpeta (str): Carpeta donde se guarda el archivo.

        Returns:
            str: Ruta del archivo generado.
        """
        campos = [
            "fecha_extraccion", "libro_id", "isbn", "libro",
            "precio_interno", "precio_web", "diferencia",
            "diferencia_porcentual", "umbral", "alerta", "url_web",
        ]
        filas: List[Dict[str, object]] = []
        for comparacion in comparaciones:
            alerta = comparacion.alerta(umbral)
            if not alerta:
                continue
            web = comparacion.precio_web
            filas.append({
                "fecha_extraccion": web.fecha_extraccion.isoformat(" "),
                "libro_id": comparacion.libro.id,
                "isbn": comparacion.libro.isbn,
                "libro": comparacion.libro.titulo,
                "precio_interno": f"{comparacion.precio_interno:.2f}",
                "precio_web": f"{web.precio:.2f}",
                "diferencia": f"{comparacion.diferencia:.2f}",
                "diferencia_porcentual": (
                    f"{comparacion.diferencia_porcentual:.2f}"
                ),
                "umbral": str(umbral),
                "alerta": alerta,
                "url_web": web.url,
            })
        os.makedirs(carpeta, exist_ok=True)
        nombre = ejecucion.strftime("alertas_%Y%m%d_%H%M%S.csv")
        archivo = ArchivoCSV(nombre, campos, carpeta)
        # Con BOM, Excel abre el archivo con las tildes correctas.
        archivo.escribir(filas, codificacion="utf-8-sig")
        return archivo.ruta


class ServicioReportes:
    """Reportes que combinan información de varias entidades."""

    def __init__(
        self,
        servicio_libro: ServicioLibro,
        servicio_precio: ServicioPrecio,
        servicio_stock: ServicioStock,
        servicio_cotizacion: ServicioCotizacionDolar,
        servicio_tipo: ServicioTipoCotizacion,
        servicio_moneda: ServicioMoneda,
    ) -> None:
        """Constructor.

        Args:
            servicio_libro (ServicioLibro): Servicio de libros.
            servicio_precio (ServicioPrecio): Servicio de precios.
            servicio_stock (ServicioStock): Servicio de stock.
            servicio_cotizacion (ServicioCotizacionDolar): Servicio de
                cotizaciones.
            servicio_tipo (ServicioTipoCotizacion): Servicio de tipos de
                cotización.
            servicio_moneda (ServicioMoneda): Servicio de monedas.
        """
        self.__libros: ServicioLibro = servicio_libro
        self.__precios: ServicioPrecio = servicio_precio
        self.__stock: ServicioStock = servicio_stock
        self.__cotizaciones: ServicioCotizacionDolar = servicio_cotizacion
        self.__tipos: ServicioTipoCotizacion = servicio_tipo
        self.__monedas: ServicioMoneda = servicio_moneda

    def precio_en_pesos(self, libro_id: int, tipo_id: int) -> Optional[float]:
        """Precio de referencia del libro en pesos.

        Si el libro tiene precio en ARS se usa ese, si no, se convierte
        el primer precio disponible con la cotización indicada.

        Args:
            libro_id (int): ID del libro.
            tipo_id (int): ID del tipo de cotización.

        Returns:
            Optional[float]: Precio en pesos, o None si el libro no
                tiene precios.
        """
        precios = self.__precios.listar_por_libro(libro_id)
        if not precios:
            return None
        return self.__en_pesos(
            precios, self.__cotizaciones.ultima(tipo_id)
        )

    def precio_en_moneda(
        self, libro_id: int, moneda: Moneda, tipo_id: int
    ) -> Optional[float]:
        """Precio del libro expresado en una moneda.

        Si el libro tiene un precio cargado en esa moneda se usa ese; si
        no, se convierte su precio en pesos con la cotización indicada.

        Args:
            libro_id (int): ID del libro.
            moneda (Moneda): Moneda en la que se quiere el precio.
            tipo_id (int): ID del tipo de cotización.

        Returns:
            Optional[float]: Precio en la moneda, o None si el libro no
                tiene precios.
        """
        precios = self.__precios.listar_por_libro(libro_id)
        if not precios:
            return None
        return self.__en_moneda(
            precios, moneda, self.__cotizaciones.ultima(tipo_id)
        )

    @staticmethod
    def __en_pesos(
        precios: List[Precio], cotizacion: CotizacionDolar
    ) -> float:
        """Precio de referencia en pesos a partir de los precios cargados.

        Args:
            precios (List[Precio]): Precios del libro (al menos uno).
            cotizacion (CotizacionDolar): Cotización para convertir.

        Returns:
            float: Precio en pesos.
        """
        precio = min(precios, key=lambda p: not p.moneda.es_local)
        if precio.moneda.es_local:
            return precio.monto
        return precio.monto * precio.moneda.equivalencia_usd * (
            cotizacion.venta
        )

    @classmethod
    def __en_moneda(
        cls,
        precios: List[Precio],
        moneda: Moneda,
        cotizacion: CotizacionDolar,
    ) -> float:
        """Precio en una moneda a partir de los precios cargados.

        Args:
            precios (List[Precio]): Precios del libro (al menos uno).
            moneda (Moneda): Moneda en la que se quiere el precio.
            cotizacion (CotizacionDolar): Cotización para convertir.

        Returns:
            float: Precio en la moneda.
        """
        for precio in precios:
            if precio.moneda.id == moneda.id:
                return precio.monto
        pesos = cls.__en_pesos(precios, cotizacion)
        if moneda.es_local:
            return pesos
        return pesos / (moneda.equivalencia_usd * cotizacion.venta)

    def __precios_por_libro(self) -> Dict[int, List[Precio]]:
        """Lee todos los precios en una sola consulta, agrupados por libro.

        Returns:
            Dict[int, List[Precio]]: Precios de cada libro por su ID.
        """
        agrupados: Dict[int, List[Precio]] = {}
        for precio in self.__precios.listar():
            agrupados.setdefault(precio.libro.id, []).append(precio)
        return agrupados

    def lista_bimonetaria(
        self, moneda_id: int, tipo_id: int
    ) -> List[Tuple[Libro, float, float]]:
        """Lista de precios de los libros en pesos y en otra moneda.

        Antes de calcular se actualizan las cotizaciones desde DolarApi;
        si no hay conexión se usa la última cotización guardada.

        Args:
            moneda_id (int): ID de la moneda a mostrar junto a los pesos.
            tipo_id (int): ID del tipo de cotización para convertir.

        Returns:
            List[Tuple[Libro, float, float]]: Filas (libro, precio en
                pesos, precio en la moneda elegida) de los libros que
                tienen precio.
        """
        moneda = self.__monedas.obtener(moneda_id)
        self.__tipos.obtener(tipo_id)
        self.__cotizaciones.refrescar()
        cotizacion = self.__cotizaciones.ultima(tipo_id)
        precios = self.__precios_por_libro()
        filas = []
        for libro in self.__libros.listar():
            del_libro = precios.get(libro.id)
            if not del_libro:
                continue
            filas.append((
                libro,
                self.__en_pesos(del_libro, cotizacion),
                self.__en_moneda(del_libro, moneda, cotizacion),
            ))
        return filas

    def exportar_precios_csv(
        self, tipo_id: int, carpeta: str = CARPETA_EXPORTACION
    ) -> str:
        """Exporta a CSV el precio de cada libro en todas las monedas.

        Se genera una columna por cada moneda activa, con el precio
        convertido usando la cotización indicada.

        Args:
            tipo_id (int): ID del tipo de cotización para convertir.
            carpeta (str): Carpeta donde se guarda el archivo.

        Returns:
            str: Ruta del archivo generado.
        """
        tipo = self.__tipos.obtener(tipo_id)
        self.__cotizaciones.refrescar()
        cotizacion = self.__cotizaciones.ultima(tipo_id)
        monedas = self.__monedas.listar()
        precios = self.__precios_por_libro()
        campos = ["libro_id", "isbn", "titulo", "tipo_dolar", "fecha_dolar"]
        campos += [moneda.codigo for moneda in monedas]
        filas: List[Dict[str, object]] = []
        for libro in self.__libros.listar():
            del_libro = precios.get(libro.id)
            if not del_libro:
                continue
            fila: Dict[str, object] = {
                "libro_id": libro.id,
                "isbn": libro.isbn,
                "titulo": libro.titulo,
                "tipo_dolar": tipo.nombre,
                "fecha_dolar": cotizacion.fecha,
            }
            for moneda in monedas:
                monto = self.__en_moneda(del_libro, moneda, cotizacion)
                fila[moneda.codigo] = f"{monto:.2f}"
            filas.append(fila)
        os.makedirs(carpeta, exist_ok=True)
        nombre = datetime.datetime.now().strftime(
            "precios_%Y%m%d_%H%M%S.csv"
        )
        archivo = ArchivoCSV(nombre, campos, carpeta)
        archivo.escribir(filas)
        return archivo.ruta

    def valor_inventario(
        self, tipo_id: int
    ) -> Tuple[List[Tuple[Stock, float]], float]:
        """Valoriza el stock en pesos con la cotización indicada.

        Antes de calcular se actualizan las cotizaciones desde DolarApi;
        si no hay conexión se usa la última cotización guardada.

        Args:
            tipo_id (int): ID del tipo de cotización.

        Returns:
            Tupla con el detalle (stock, subtotal) y el total general.
        """
        self.__cotizaciones.refrescar()
        cotizacion = self.__cotizaciones.ultima(tipo_id)
        precios = self.__precios_por_libro()
        detalle: List[Tuple[Stock, float]] = []
        for stock in self.__stock.listar():
            del_libro = precios.get(stock.libro_id)
            if del_libro:
                precio = self.__en_pesos(del_libro, cotizacion)
                detalle.append((stock, precio * stock.cantidad))
        return detalle, sum(subtotal for _, subtotal in detalle)

    def cotizar_libro(
        self, libro_id: int
    ) -> List[Tuple[TipoCotizacion, CotizacionDolar, Precio, float]]:
        """Cotiza cada precio en moneda extranjera de un libro con la
        última cotización de cada tipo de dólar disponible.

        Antes de calcular se actualizan las cotizaciones desde DolarApi;
        si no hay conexión se usa la última cotización guardada.

        Args:
            libro_id (int): ID del libro.

        Returns:
            List[Tuple[TipoCotizacion, CotizacionDolar, Precio, float]]:
                Filas (tipo, cotización, precio, importe en pesos).
        """
        self.__libros.obtener(libro_id)
        self.__cotizaciones.refrescar()
        extranjeros = [
            precio for precio in self.__precios.listar_por_libro(libro_id)
            if not precio.moneda.es_local
        ]
        ultimas: List[Tuple[TipoCotizacion, CotizacionDolar]] = []
        if extranjeros:
            for tipo in self.__tipos.listar():
                try:
                    ultimas.append(
                        (tipo, self.__cotizaciones.ultima(tipo.id))
                    )
                except ValueError:
                    continue
        filas = []
        for precio in extranjeros:
            for tipo, cotizacion in ultimas:
                pesos = precio.monto * precio.moneda.equivalencia_usd * (
                    cotizacion.venta
                )
                filas.append((tipo, cotizacion, precio, pesos))
        return filas


@dataclass
class Servicios:
    """Agrupa todos los servicios del sistema."""

    generos: ServicioGenero
    editoriales: ServicioEditorial
    monedas: ServicioMoneda
    tipos_cotizacion: ServicioTipoCotizacion
    libros: ServicioLibro
    precios: ServicioPrecio
    stock: ServicioStock
    cotizaciones: ServicioCotizacionDolar
    reportes: ServicioReportes
    precios_web: ServicioPrecioWeb
    competencia: ServicioCompetencia


def crear_servicios(repos: Repositorios) -> Servicios:
    """Instancia los servicios a partir de los repositorios.

    Args:
        repos (Repositorios): Repositorios del sistema.

    Returns:
        Servicios: Los servicios del sistema.
    """
    tipos = ServicioTipoCotizacion(repos.tipos_cotizacion, repos.cotizaciones)
    libros = ServicioLibro(repos.libros, repos.precios, repos.stock)
    precios = ServicioPrecio(repos.precios)
    stock = ServicioStock(repos.stock)
    cotizaciones = ServicioCotizacionDolar(repos.cotizaciones, tipos)
    monedas = ServicioMoneda(repos.monedas, repos.precios)
    reportes = ServicioReportes(
        libros, precios, stock, cotizaciones, tipos, monedas
    )
    precios_web = ServicioPrecioWeb(repos.precios_web)
    return Servicios(
        generos=ServicioGenero(repos.generos, repos.libros),
        editoriales=ServicioEditorial(repos.editoriales, repos.libros),
        monedas=monedas,
        tipos_cotizacion=tipos,
        libros=libros,
        precios=precios,
        stock=stock,
        cotizaciones=cotizaciones,
        reportes=reportes,
        precios_web=precios_web,
        competencia=ServicioCompetencia(
            libros, precios_web, reportes, cotizaciones
        ),
    )
