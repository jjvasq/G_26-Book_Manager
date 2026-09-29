"""Servicios con la lógica de negocio de Book Manager."""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Callable, Dict, Generic, List, Optional, Tuple, TypeVar

import requests

from book_manager.entities.entities import (
    CotizacionDolar,
    Editorial,
    EntidadId,
    Genero,
    Libro,
    Moneda,
    Precio,
    Stock,
    TipoCotizacion,
)
from book_manager.repositories.repositories import (
    IRepositorio,
    IRepositorioCotizacionDolar,
    IRepositorioStock,
    RepositorioLibro,
    RepositorioPrecio,
    RepositorioStock,
    Repositorios,
)

T = TypeVar("T", bound=EntidadId)

URL_DOLAR_API = "https://dolarapi.com/v1/dolares"

# Minutos durante los que una consulta a DolarApi se considera vigente.
MINUTOS_VIGENCIA_COTIZACION = 5

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
            ValueError: Si no existe.
        """
        entidad = self.__repositorio.leer_por_id(id)
        if entidad is None:
            raise ValueError(f"No existe un registro con ID {id}.")
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
            ValueError: Si otro registro ya tiene ese valor.
        """
        valor = valor.strip().lower()
        for otra in self.__repositorio.leer_todos():
            if otra.id != id and atributo(otra).lower() == valor:
                raise ValueError(
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
            ValueError: Si el nombre ya está en uso.
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
            ValueError: Si hay registros que dependen de este.
        """
        if any(
            libro.genero.id == id for libro in self.__repo_libro.leer_todos()
        ):
            raise ValueError(
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
            ValueError: Si el nombre ya está en uso.
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
            ValueError: Si hay registros que dependen de este.
        """
        libros = self.__repo_libro.leer_todos()
        if any(libro.editorial.id == id for libro in libros):
            raise ValueError(
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
            ValueError: Si el código ya está en uso.
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
            ValueError: Si hay registros que dependen de este.
        """
        if self.__repo_precio.leer_por_moneda(id):
            raise ValueError(
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
            ValueError: Si el nombre ya está en uso.
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
            ValueError: Si hay registros que dependen de este.
        """
        if self.__repo_cotizacion.leer_historico_por_tipo(id):
            raise ValueError(
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
            ValueError: Si el ISBN ya lo tiene otro libro.
        """
        existente = self.__repo_libro.leer_por_isbn(isbn)
        if existente is not None and existente.id != id:
            raise ValueError("Ya existe un libro con ese ISBN.")

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
            ValueError: Si el libro ya tiene un precio en esa moneda.
        """
        for otro in self.__repo_precio.leer_por_libro(libro_id):
            if otro.id != id and otro.moneda.id == moneda_id:
                raise ValueError(
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
            ValueError: Si el libro no tiene stock registrado.
        """
        stock = self.__repositorio.leer_por_libro(libro_id)
        if stock is None:
            raise ValueError(f"El libro {libro_id} no tiene stock registrado.")
        return stock

    def verificar_sin_stock(self, libro_id: int) -> None:
        """Verifica que el libro todavía no tenga stock registrado.

        Args:
            libro_id (int): ID del libro.

        Raises:
            ValueError: Si el libro ya tiene stock.
        """
        if self.__repositorio.leer_por_libro(libro_id) is not None:
            raise ValueError(
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


class ServicioCotizacion:
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

    @property
    def ultima_consulta(self) -> Optional[datetime.datetime]:
        """Momento de la última consulta exitosa a DolarApi."""
        return self.__ultima_consulta

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
            self.actualizar_desde_api(timeout=5)
        except RuntimeError:
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
            ValueError: Si no existe.
        """
        cotizacion = self.__repositorio.leer_por_tipo_y_fecha(tipo_id, fecha)
        if cotizacion is None:
            raise ValueError("No existe una cotización para ese tipo y fecha.")
        return cotizacion

    def ultima(self, tipo_id: int) -> CotizacionDolar:
        """Devuelve la cotización más reciente de un tipo.

        Args:
            tipo_id (int): ID del tipo de cotización.

        Returns:
            CotizacionDolar: La cotización más reciente.

        Raises:
            ValueError: Si no hay cotizaciones de ese tipo.
        """
        historico = self.historico(tipo_id)
        if not historico:
            raise ValueError("No hay cotizaciones cargadas para ese tipo.")
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
            ValueError: Si la fecha es futura o ya hay una cotización de
                ese tipo en esa fecha.
        """
        if fecha > datetime.date.today():
            raise ValueError("No se pueden cargar cotizaciones futuras.")
        if self.__repositorio.leer_por_tipo_y_fecha(tipo_id, fecha):
            raise ValueError(
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

    def actualizar_desde_api(
        self, timeout: float = 10
    ) -> List[CotizacionDolar]:
        """Descarga las cotizaciones del día desde DolarApi.

        Solo se registran los tipos que existen en el sistema. Si ya hay
        una cotización para ese tipo en la fecha, se actualiza.

        Args:
            timeout (float): Segundos máximos de espera de la API.

        Returns:
            List[CotizacionDolar]: Cotizaciones creadas o actualizadas.

        Raises:
            RuntimeError: Si no se pudo consultar la API.
        """
        try:
            respuesta = requests.get(URL_DOLAR_API, timeout=timeout)
            respuesta.raise_for_status()
            datos = respuesta.json()
        except (requests.RequestException, ValueError) as error:
            raise RuntimeError(
                f"No se pudo consultar la cotización: {error}"
            ) from error

        self.__ultima_consulta = datetime.datetime.now()
        registradas: List[CotizacionDolar] = []
        for dato in datos:
            nombre = CASAS_DOLAR_API.get(dato.get("casa", ""))
            tipo = self.__servicio_tipo.buscar_por_nombre(nombre or "")
            venta = dato.get("venta")
            if tipo is None or not venta:
                continue
            compra = dato.get("compra") or venta
            fecha = datetime.date.fromisoformat(
                str(dato.get("fechaActualizacion", ""))[:10]
                or datetime.date.today().isoformat()
            )
            registradas.append(
                self.__registrar(tipo, fecha, float(compra), float(venta))
            )
        return registradas

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


class ServicioReportes:
    """Reportes que combinan información de varias entidades."""

    def __init__(
        self,
        servicio_libro: ServicioLibro,
        servicio_precio: ServicioPrecio,
        servicio_stock: ServicioStock,
        servicio_cotizacion: ServicioCotizacion,
        servicio_tipo: ServicioTipoCotizacion,
    ) -> None:
        """Constructor.

        Args:
            servicio_libro (ServicioLibro): Servicio de libros.
            servicio_precio (ServicioPrecio): Servicio de precios.
            servicio_stock (ServicioStock): Servicio de stock.
            servicio_cotizacion (ServicioCotizacion): Servicio de
                cotizaciones.
            servicio_tipo (ServicioTipoCotizacion): Servicio de tipos de
                cotización.
        """
        self.__libros: ServicioLibro = servicio_libro
        self.__precios: ServicioPrecio = servicio_precio
        self.__stock: ServicioStock = servicio_stock
        self.__cotizaciones: ServicioCotizacion = servicio_cotizacion
        self.__tipos: ServicioTipoCotizacion = servicio_tipo

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
        precios.sort(key=lambda p: not p.moneda.es_local)
        precio = precios[0]
        return self.__cotizaciones.convertir_a_pesos(
            precio.monto, precio.moneda, tipo_id
        )

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
        detalle: List[Tuple[Stock, float]] = []
        for stock in self.__stock.listar():
            precio = self.precio_en_pesos(stock.libro_id, tipo_id)
            if precio is not None:
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
        filas = []
        for precio in self.__precios.listar_por_libro(libro_id):
            if precio.moneda.es_local:
                continue
            for tipo in self.__tipos.listar():
                try:
                    cotizacion = self.__cotizaciones.ultima(tipo.id)
                except ValueError:
                    continue
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
    cotizaciones: ServicioCotizacion
    reportes: ServicioReportes


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
    cotizaciones = ServicioCotizacion(repos.cotizaciones, tipos)
    return Servicios(
        generos=ServicioGenero(repos.generos, repos.libros),
        editoriales=ServicioEditorial(repos.editoriales, repos.libros),
        monedas=ServicioMoneda(repos.monedas, repos.precios),
        tipos_cotizacion=tipos,
        libros=libros,
        precios=precios,
        stock=stock,
        cotizaciones=cotizaciones,
        reportes=ServicioReportes(
            libros, precios, stock, cotizaciones, tipos
        ),
    )
