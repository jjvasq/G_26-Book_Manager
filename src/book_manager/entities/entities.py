"""Definición de entidades del sistema Book Manager."""
from __future__ import annotations

import datetime
from abc import ABC


def texto_a_fecha(texto: str) -> datetime.date:
    """Convierte un texto con formato AAAA-MM-DD en una fecha.

    Args:
        texto (str): Fecha en formato AAAA-MM-DD.

    Returns:
        datetime.date: La fecha obtenida.

    Raises:
        ValueError: Si el texto no tiene el formato AAAA-MM-DD o la fecha
            no existe.
    """
    partes = texto.strip().split("-")
    if len(partes) != 3:
        raise ValueError(f"Fecha inválida: '{texto}'. Use AAAA-MM-DD.")
    anio, mes, dia = partes
    return datetime.date(int(anio), int(mes), int(dia))


def _validar_texto(valor: str, campo: str) -> str:
    """Valida que un texto no esté vacío y lo devuelve sin espacios.

    Args:
        valor (str): Valor a validar.
        campo (str): Nombre del campo, para el mensaje de error.

    Returns:
        str: El texto sin espacios atras o adelante.
    """
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(f"El campo '{campo}' no puede estar vacío.")
    return valor.strip()


def _validar_decimal(valor: float, campo: str) -> float:
    """Valida que un valor numérico sea mayor a cero.

    Args:
        valor (float): Valor a validar.
        campo (str): Nombre del campo, para el mensaje de error.

    Returns:
        float: El valor como float.
    """
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ValueError(f"El campo '{campo}' debe ser numérico.")
    if valor <= 0:
        raise ValueError(f"El campo '{campo}' debe ser mayor a cero.")
    return float(valor)


def _validar_entero(valor: int, campo: str, minimo: int = 0) -> int:
    """Valida que un valor sea un entero mayor o igual a un mínimo.

    Args:
        valor (int): Valor a validar.
        campo (str): Nombre del campo, para el mensaje de error.
        minimo (int): Valor mínimo ingresado.

    Returns:
        int: El valor validado.
    """
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise ValueError(f"El campo '{campo}' debe ser un número entero.")
    if valor < minimo:
        raise ValueError(
            f"El campo '{campo}' debe ser mayor o igual a {minimo}."
        )
    return valor


class EntidadId(ABC):
    """Clase EntidadId para las entidades identificadas por un ID entero.

    Un ID igual a 0 indica que la entidad todavía no fue almacenada,
    el repositorio le asigna el próximo ID disponible al crearla.
    """

    def __init__(self, id: int = 0) -> None:
        """Constructor.

        Args:
            id (int): ID de la entidad (0 si todavía no fue almacenada).
        """
        self.id: int = id

    @property
    def id(self) -> int:
        """Id de la entidad."""
        return self.__id

    @id.setter
    def id(self, valor: int) -> None:
        self.__id: int = _validar_entero(valor, "id")

    def __eq__(self, otro: object) -> bool:
        """Compara dos entidades por Id y Tipo.

        Args:
            otro (object): Objeto a comparar.

        Returns:
            bool: True si son la misma entidad.
        """
        return type(self) is type(otro) and self.id == otro.id

    def __hash__(self) -> int:
        """Hash de la entidad.

        Returns:
            int: Hash basado en el Tipo y el ID.
        """
        return hash((type(self).__name__, self.id))


class Genero(EntidadId):
    """ Genero literario al que pertenece un libro."""

    def __init__(self, id: int, nombre: str, descripcion: str = "") -> None:
        """Constructor.

        Args:
            id (int): ID de la entidad (0 si todavía no fue almacenada).
            nombre (str): Nombre del género.
            descripcion (str): Descripción.
        """
        super().__init__(id)
        self.nombre: str = nombre
        self.descripcion: str = descripcion

    @property
    def nombre(self) -> str:
        """Nombre del género."""
        return self.__nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        self.__nombre: str = _validar_texto(valor, "nombre")

    @property
    def descripcion(self) -> str:
        """Descripción opcional del género."""
        return self.__descripcion

    @descripcion.setter
    def descripcion(self, valor: str) -> None:
        self.__descripcion: str = (valor or "").strip()

    def __str__(self) -> str:
        """ Representacion clara del objeto.

        Returns:
            str: Representacion clara del objeto.
        """
        return f"[{self.id}] {self.nombre} - {self.descripcion}"


class Editorial(EntidadId):
    """ Editorial de Liberos """

    def __init__(self, id: int, nombre: str, pais: str, email: str) -> None:
        """Constructor.

        Args:
            id (int): ID de la entidad (0 si todavía no fue almacenada).
            nombre (str): Nombre de la editorial.
            pais (str): País de origen.
            email (str): Correo.
        """
        super().__init__(id)
        self.nombre: str = nombre
        self.pais: str = pais
        self.email: str = email

    @property
    def nombre(self) -> str:
        """Nombre de la editorial."""
        return self.__nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        self.__nombre: str = _validar_texto(valor, "nombre")

    @property
    def pais(self) -> str:
        """País de origen de la editorial."""
        return self.__pais

    @pais.setter
    def pais(self, valor: str) -> None:
        self.__pais: str = _validar_texto(valor, "país")

    @property
    def email(self) -> str:
        """Correo de contacto."""
        return self.__email

    @email.setter
    def email(self, valor: str) -> None:
        valor = _validar_texto(valor, "email")
        if "@" not in valor or "." not in valor.split("@")[-1]:
            raise ValueError("El email no tiene un formato válido.")
        self.__email: str = valor

    def __str__(self) -> str:
        """Representacion clara del objeto.

        Returns:
            str: Representacion clara del objeto.
        """
        return f"[{self.id}] {self.nombre} ({self.pais}) - {self.email}"


class Moneda(EntidadId):
    """Moneda en la que se puede expresar un precio. """

    CODIGO_LOCAL = "ARS"

    def __init__(
        self,
        id: int,
        codigo: str,
        nombre: str,
        simbolo: str,
        equivalencia_usd: float,
    ) -> None:
        """Constructor.

        Args:
            id (int): ID de la entidad (0 si todavía no fue almacenada).
            codigo (str): Código identificador de la moneda.
            nombre (str): Nombre de la moneda.
            simbolo (str): Símbolo de la moneda.
            equivalencia_usd (float): Valor en dólares de una unidad de la
                moneda.
        """
        super().__init__(id)
        self.codigo: str = codigo
        self.nombre: str = nombre
        self.simbolo: str = simbolo
        self.equivalencia_usd: float = equivalencia_usd

    @property
    def codigo(self) -> str:
        """Código identificatorio de la moneda (ARS, USD, EUR...)."""
        return self.__codigo

    @codigo.setter
    def codigo(self, valor: str) -> None:
        valor = _validar_texto(valor, "código").upper()
        if len(valor) != 3 or not valor.isalpha():
            raise ValueError("El código de moneda debe tener 3 letras.")
        self.__codigo: str = valor

    @property
    def nombre(self) -> str:
        """Nombre de la moneda."""
        return self.__nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        self.__nombre: str = _validar_texto(valor, "nombre")

    @property
    def simbolo(self) -> str:
        """Símbolo de la moneda ($, US$, €...)."""
        return self.__simbolo

    @simbolo.setter
    def simbolo(self, valor: str) -> None:
        self.__simbolo: str = _validar_texto(valor, "símbolo")

    @property
    def equivalencia_usd(self) -> float:
        """Valor en dólares de una unidad de la moneda."""
        return self.__equivalencia_usd

    @equivalencia_usd.setter
    def equivalencia_usd(self, valor: float) -> None:
        self.__equivalencia_usd: float = _validar_decimal(
            valor, "equivalencia USD"
        )

    @property
    def es_local(self) -> bool:
        """Indica si la moneda es el peso argentino."""
        return self.codigo == self.CODIGO_LOCAL

    def __str__(self) -> str:
        """Representacion clara del objeto.

        Returns:
            str: Representacion clara del objeto.
        """
        return (
            f"[{self.id}] {self.codigo} - {self.nombre} ({self.simbolo}) "
            f"| 1 {self.codigo} = {self.equivalencia_usd:g} USD"
        )


class TipoCotizacion(EntidadId):
    """Tipo de cotización del dólar (Oficial, Blue, MEP, etc.)."""

    def __init__(self, id: int, nombre: str, descripcion: str = "") -> None:
        """Constructor.

        Args:
            id (int): ID de la entidad (0 si todavía no fue almacenada).
            nombre (str): Nombre del tipo de cotización.
            descripcion (str): Descripción opcional.
        """
        super().__init__(id)
        self.nombre: str = nombre
        self.descripcion: str = descripcion

    @property
    def nombre(self) -> str:
        """Nombre del tipo de cotización."""
        return self.__nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        self.__nombre: str = _validar_texto(valor, "nombre")

    @property
    def descripcion(self) -> str:
        """Descripción opcional del tipo de cotización."""
        return self.__descripcion

    @descripcion.setter
    def descripcion(self, valor: str) -> None:
        self.__descripcion: str = (valor or "").strip()

    def __str__(self) -> str:
        """Representacion clara del objeto.

        Returns:
            str: Representacion clara del objeto.
        """
        return f"[{self.id}] {self.nombre} - {self.descripcion}"


class Libro(EntidadId):
    """Título del catálogo de la librería."""

    def __init__(
        self,
        id: int,
        isbn: str,
        titulo: str,
        autor: str,
        anio: int,
        genero: Genero,
        editorial: Editorial,
    ) -> None:
        """Constructor.

        Args:
            id (int): ID de la entidad (0 si todavía no fue almacenada).
            isbn (str): ISBN de 10 o 13 caracteres.
            titulo (str): Título del libro.
            autor (str): Autor del libro.
            anio (int): Año de publicación.
            genero (Genero): Género del libro.
            editorial (Editorial): Editorial del libro.
        """
        super().__init__(id)
        self.isbn: str = isbn
        self.titulo: str = titulo
        self.autor: str = autor
        self.anio: int = anio
        self.genero: Genero = genero
        self.editorial: Editorial = editorial

    @property
    def isbn(self) -> str:
        """ISBN de 10 o 13 caracteres, sin guiones."""
        return self.__isbn

    @isbn.setter
    def isbn(self, valor: str) -> None:
        valor = _validar_texto(valor, "ISBN").replace("-", "").replace(" ", "")
        es_isbn10 = len(valor) == 10 and valor[:9].isdigit() and (
            valor[9].isdigit() or valor[9].upper() == "X"
        )
        es_isbn13 = len(valor) == 13 and valor.isdigit()
        if not (es_isbn10 or es_isbn13):
            raise ValueError("El ISBN debe tener 10 o 13 caracteres.")
        self.__isbn: str = valor.upper()

    @property
    def titulo(self) -> str:
        """Título del libro."""
        return self.__titulo

    @titulo.setter
    def titulo(self, valor: str) -> None:
        self.__titulo: str = _validar_texto(valor, "título")

    @property
    def autor(self) -> str:
        """Autor o autores del libro."""
        return self.__autor

    @autor.setter
    def autor(self, valor: str) -> None:
        self.__autor: str = _validar_texto(valor, "autor")

    @property
    def anio(self) -> int:
        """Año de publicación."""
        return self.__anio

    @anio.setter
    def anio(self, valor: int) -> None:
        valor = _validar_entero(valor, "año", minimo=1450)
        if valor > datetime.date.today().year:
            raise ValueError("El año de publicación no puede ser futuro.")
        self.__anio: int = valor

    @property
    def genero(self) -> Genero:
        """Género literario del libro."""
        return self.__genero

    @genero.setter
    def genero(self, valor: Genero) -> None:
        if not isinstance(valor, Genero):
            raise ValueError("El género debe ser una instancia de Genero.")
        self.__genero: Genero = valor

    @property
    def editorial(self) -> Editorial:
        """Editorial que provee el libro."""
        return self.__editorial

    @editorial.setter
    def editorial(self, valor: Editorial) -> None:
        if not isinstance(valor, Editorial):
            raise ValueError(
                "La editorial debe ser una instancia de Editorial."
            )
        self.__editorial: Editorial = valor

    def __str__(self) -> str:
        """Representacion clara del objeto.

        Returns:
            str: Representacion clara del objeto.
        """
        return (
            f"[{self.id}] {self.titulo} - {self.autor} ({self.anio}) "
            f"| ISBN {self.isbn} | {self.genero.nombre} "
            f"| {self.editorial.nombre}"
        )


class Precio(EntidadId):
    """Valor monetario de un libro expresado en una moneda."""

    def __init__(
        self, id: int, libro: Libro, moneda: Moneda, monto: float
    ) -> None:
        """Constructor.

        Args:
            id (int): ID de la entidad (0 si todavía no fue almacenada).
            libro (Libro): Libro asociado.
            moneda (Moneda): Moneda del importe.
            monto (float): Importe.
        """
        super().__init__(id)
        self.libro: Libro = libro
        self.moneda: Moneda = moneda
        self.monto: float = monto

    @property
    def libro(self) -> Libro:
        """Libro al que corresponde el precio."""
        return self.__libro

    @libro.setter
    def libro(self, valor: Libro) -> None:
        if not isinstance(valor, Libro):
            raise ValueError("El libro debe ser una instancia de Libro.")
        self.__libro: Libro = valor

    @property
    def moneda(self) -> Moneda:
        """Moneda en la que está expresado el precio."""
        return self.__moneda

    @moneda.setter
    def moneda(self, valor: Moneda) -> None:
        if not isinstance(valor, Moneda):
            raise ValueError("La moneda debe ser una instancia de Moneda.")
        self.__moneda: Moneda = valor

    @property
    def monto(self) -> float:
        """Importe del precio."""
        return self.__monto

    @monto.setter
    def monto(self, valor: float) -> None:
        self.__monto: float = _validar_decimal(valor, "monto")

    def __str__(self) -> str:
        """Representacion clara del objeto.

        Returns:
            str: Representacion clara del objeto.
        """
        return (
            f"[{self.id}] {self.libro.titulo}: "
            f"{self.moneda.simbolo} {self.monto:,.2f} ({self.moneda.codigo})"
        )


class Stock:
    """Cantidad disponible de un libro. Se identifica por el libro."""

    def __init__(
        self, libro: Libro, cantidad: int, stock_minimo: int = 0
    ) -> None:
        """Constructor.

        Args:
            libro (Libro): Libro asociado.
            cantidad (int): Unidades disponibles.
            stock_minimo (int): Cantidad mínima deseada.
        """
        self.libro: Libro = libro
        self.cantidad: int = cantidad
        self.stock_minimo: int = stock_minimo

    @property
    def libro(self) -> Libro:
        """Libro al que corresponde el stock."""
        return self.__libro

    @libro.setter
    def libro(self, valor: Libro) -> None:
        if not isinstance(valor, Libro):
            raise ValueError("El libro debe ser una instancia de Libro.")
        self.__libro: Libro = valor

    @property
    def libro_id(self) -> int:
        """ID del libro asociado."""
        return self.libro.id

    @property
    def cantidad(self) -> int:
        """Unidades disponibles."""
        return self.__cantidad

    @cantidad.setter
    def cantidad(self, valor: int) -> None:
        self.__cantidad: int = _validar_entero(valor, "cantidad")

    @property
    def stock_minimo(self) -> int:
        """Cantidad mínima deseada antes de reponer."""
        return self.__stock_minimo

    @stock_minimo.setter
    def stock_minimo(self, valor: int) -> None:
        self.__stock_minimo: int = _validar_entero(valor, "stock mínimo")

    @property
    def bajo_minimo(self) -> bool:
        """Indica si la cantidad está por debajo del mínimo."""
        return self.cantidad < self.stock_minimo

    def ingresar(self, unidades: int) -> None:
        """Suma unidades al stock.

        Args:
            unidades (int): Cantidad de unidades.
        """
        self.cantidad += _validar_entero(unidades, "unidades", minimo=1)

    def retirar(self, unidades: int) -> None:
        """Descuenta unidades del stock.

        Args:
            unidades (int): Cantidad de unidades.

        Raises:
            ValueError: Si no hay unidades suficientes.
        """
        unidades = _validar_entero(unidades, "unidades", minimo=1)
        if unidades > self.cantidad:
            raise ValueError(
                f"Stock insuficiente: hay {self.cantidad} unidades."
            )
        self.cantidad -= unidades

    def __str__(self) -> str:
        """Representacion clara del objeto.

        Returns:
            str: Representacion clara del objeto.
        """
        alerta = " ALERTA, hay stock mínimo!!" if self.bajo_minimo else ""
        return (
            f"[Libro {self.libro_id}] {self.libro.titulo}: "
            f"{self.cantidad} u. (mínimo {self.stock_minimo}){alerta}"
        )


class CotizacionDolar:
    """Cotización del dólar para un tipo y una fecha determinados."""

    def __init__(
        self,
        tipo: TipoCotizacion,
        fecha: datetime.date,
        compra: float,
        venta: float,
    ) -> None:
        """Constructor.

        Args:
            tipo (TipoCotizacion): Tipo de cotización.
            fecha (datetime.date): Fecha de la cotización.
            compra (float): Valor de compra en pesos.
            venta (float): Valor de venta en pesos.
        """
        self.tipo: TipoCotizacion = tipo
        self.fecha: datetime.date = fecha
        self.compra: float = compra
        self.venta: float = venta

    @property
    def tipo(self) -> TipoCotizacion:
        """Tipo de cotización."""
        return self.__tipo

    @tipo.setter
    def tipo(self, valor: TipoCotizacion) -> None:
        if not isinstance(valor, TipoCotizacion):
            raise ValueError(
                "El tipo debe ser una instancia de TipoCotizacion."
            )
        self.__tipo: TipoCotizacion = valor

    @property
    def tipo_id(self) -> int:
        """ID del tipo de cotización."""
        return self.tipo.id

    @property
    def fecha(self) -> datetime.date:
        """Fecha de la cotización."""
        return self.__fecha

    @fecha.setter
    def fecha(self, valor: datetime.date) -> None:
        if isinstance(valor, datetime.datetime):
            valor = valor.date()
        if not isinstance(valor, datetime.date):
            raise ValueError("La fecha debe ser un datetime.date.")
        self.__fecha: datetime.date = valor

    @property
    def compra(self) -> float:
        """Valor de compra en pesos."""
        return self.__compra

    @compra.setter
    def compra(self, valor: float) -> None:
        self.__compra: float = _validar_decimal(valor, "compra")

    @property
    def venta(self) -> float:
        """Valor de venta en pesos."""
        return self.__venta

    @venta.setter
    def venta(self, valor: float) -> None:
        self.__venta: float = _validar_decimal(valor, "venta")

    def __str__(self) -> str:
        """Representacion clara del objeto.

        Returns:
            str: Representacion clara del objeto.
        """
        return (
            f"{self.fecha} | {self.tipo.nombre:<10} "
            f"| compra $ {self.compra:,.2f} | venta $ {self.venta:,.2f}"
        )
