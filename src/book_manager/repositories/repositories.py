"""Repositorios de almacenamiento en archivos CSV."""

from __future__ import annotations

import abc
import datetime
from dataclasses import dataclass
from typing import Dict, Generic, Iterable, List, Optional, Tuple, TypeVar

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
    texto_a_fecha,
)

# Carpeta migrations/csv, a partir de la ubicación de este archivo.
CSV_DIR = "/".join(__file__.replace("\\", "/").split("/")[:-2]) + (
    "/migrations/csv"
)

# Valores de la columna `estado` de los CSV (borrado lógico).
ACTIVO = 1
BORRADO = 0

T = TypeVar("T", bound=EntidadId)


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


def _leer_estado(fila: Dict[str, str]) -> int:
    """Obtiene el estado de una fila leída del CSV.

    Si la fila no tiene la columna `estado` (archivos anteriores al
    borrado lógico) se la considera activa.

    Args:
        fila (Dict[str, str]): Fila leída del CSV.

    Returns:
        int: ACTIVO (1) o BORRADO (0).
    """
    return int(fila.get("estado") or ACTIVO)


class RepositorioCSV(IRepositorio[T]):
    """Implementación genérica de IRepositorio almacenada en CSV.

    Las subclases definen el nombre del archivo, las columnas y cómo
    convertir una entidad en fila y viceversa.

    El borrado es lógico: cada fila tiene una columna `estado` (1 = activo,
    0 = borrado). Los registros borrados se conservan en el archivo y en
    memoria para no perder las referencias, pero las lecturas públicas
    solo devuelven los activos.
    """

    ARCHIVO: str = ""
    CAMPOS: List[str] = []

    def __init__(self, directorio: str = CSV_DIR) -> None:
        """Constructor.

        Args:
            directorio (str): Carpeta donde se guardan los CSV.
        """
        self.__archivo: ArchivoCSV = ArchivoCSV(
            self.ARCHIVO, self.CAMPOS, directorio
        )
        self.__entidades: Dict[int, T] = {}
        self.__estados: Dict[int, int] = {}
        self._cargar()

    def _cargar(self) -> None:
        """Carga en memoria las entidades guardadas en el archivo."""
        self.__entidades = {}
        self.__estados = {}
        for fila in self.__archivo.leer():
            entidad = self._desde_fila(fila)
            self.__entidades[entidad.id] = entidad
            self.__estados[entidad.id] = _leer_estado(fila)

    def _guardar(self) -> None:
        """Almacena en el archivo todas las entidades, con su estado."""
        filas = []
        for clave in sorted(self.__entidades):
            fila = self._a_fila(self.__entidades[clave])
            fila["estado"] = self.__estados[clave]
            filas.append(fila)
        self.__archivo.escribir(filas)

    def _esta_activa(self, id: int) -> bool:
        """Indica si existe una entidad activa con ese ID.

        Args:
            id (int): ID del registro.

        Returns:
            bool: True si existe y no está borrada.
        """
        return self.__estados.get(id) == ACTIVO

    def _proximo_id(self) -> int:
        """Calcula el próximo ID disponible (sin reutilizar los borrados).

        Returns:
            int: El próximo ID libre.
        """
        return max(self.__entidades, default=0) + 1

    def crear(self, entidad: T) -> T:
        """Crea un nuevo registro en el repositorio.

        Args:
            entidad (T): Entidad a procesar.

        Returns:
            T: La entidad creada.

        Raises:
            ValueError: Si ya existe una entidad con el mismo ID (aunque
                esté borrada).
        """
        if entidad.id == 0:
            entidad.id = self._proximo_id()
        if entidad.id in self.__entidades:
            raise ValueError(f"Ya existe una entidad con ID {entidad.id}.")
        self.__entidades[entidad.id] = entidad
        self.__estados[entidad.id] = ACTIVO
        self._guardar()
        return entidad

    def leer_por_id(self, id: int) -> Optional[T]:
        """Lee una entidad activa por su ID.

        Args:
            id (int): ID del registro.

        Returns:
            Optional[T]: La entidad si existe y está activa, None en caso
                contrario.
        """
        if not self._esta_activa(id):
            return None
        return self.__entidades[id]

    def leer_incluso_borrado(self, id: int) -> Optional[T]:
        """Lee una entidad por su ID, esté activa o borrada.

        Se usa para resolver las referencias entre entidades al cargar
        los archivos.

        Args:
            id (int): ID del registro.

        Returns:
            Optional[T]: La entidad si existe, None en caso contrario.
        """
        return self.__entidades.get(id)

    def leer_todos(self) -> List[T]:
        """Lee todas las entidades activas.

        Returns:
            List[T]: Lista de las entidades activas.
        """
        return [
            self.__entidades[clave]
            for clave in sorted(self.__entidades)
            if self._esta_activa(clave)
        ]

    def actualizar(self, entidad: T) -> T:
        """Actualiza la entidad guardada con los datos de `entidad`.

        Se modifica el objeto existente (en lugar de reemplazarlo) para
        que las demás entidades que lo referencian vean los cambios.

        Args:
            entidad (T): Entidad a procesar.

        Returns:
            T: La entidad actualizada.

        Raises:
            ValueError: Si no existe una entidad activa con ese ID.
        """
        existente = self.leer_por_id(entidad.id)
        if existente is None:
            raise ValueError(f"No existe una entidad con ID {entidad.id}.")
        if existente is not entidad:
            self._copiar(existente, entidad)
        self._guardar()
        return existente

    def eliminar(self, id: int) -> bool:
        """Borra lógicamente un registro (estado = 0).

        Args:
            id (int): ID del registro.

        Returns:
            bool: True si se borró, False si no existía o ya estaba
                borrado.
        """
        if not self._esta_activa(id):
            return False
        self.__estados[id] = BORRADO
        self._guardar()
        return True

    @abc.abstractmethod
    def _a_fila(self, entidad: T) -> Dict[str, object]:
        """Convierte una entidad en una fila de CSV.

        Args:
            entidad (T): Entidad a procesar.

        Returns:
            Dict[str, object]: Diccionario con las columnas del CSV.
        """

    @abc.abstractmethod
    def _desde_fila(self, fila: Dict[str, str]) -> T:
        """Obtiene una entidad a partir de una fila de CSV.

        Args:
            fila (Dict[str, str]): Fila leída del CSV.

        Returns:
            T: La entidad obtenida.
        """

    @abc.abstractmethod
    def _copiar(self, destino: T, origen: T) -> None:
        """Copia los datos de `origen` en `destino` usando sus setters.

        Args:
            destino (T): Entidad guardada que se modifica.
            origen (T): Entidad con los datos nuevos.
        """


def _resolver(repositorio: RepositorioCSV, id: int, nombre: str) -> EntidadId:
    """Obtiene una entidad relacionada o lanza error si no existe.

    También encuentra las entidades borradas, para que un registro que
    las referencia (por ejemplo, un precio de un libro borrado) se pueda
    seguir cargando.

    Args:
        repositorio (RepositorioCSV): Repositorio donde buscar.
        id (int): ID a buscar.
        nombre (str): Nombre de la entidad, para el mensaje de error.

    Returns:
        EntidadId: La entidad encontrada.
    """
    entidad = repositorio.leer_incluso_borrado(id)
    if entidad is None:
        raise ValueError(f"{nombre} con ID {id} inexistente en los datos.")
    return entidad


class RepositorioGenero(RepositorioCSV[Genero]):
    """Repositorio CSV de géneros."""

    ARCHIVO = "generos.csv"
    CAMPOS = ["id", "nombre", "descripcion", "estado"]

    def _a_fila(self, entidad: Genero) -> Dict[str, object]:
        """Convierte la entidad en una fila del CSV.

        Args:
            entidad (Genero): Entidad a procesar.

        Returns:
            Dict[str, object]: Diccionario con las columnas del CSV.
        """
        return {
            "id": entidad.id,
            "nombre": entidad.nombre,
            "descripcion": entidad.descripcion,
        }

    def _desde_fila(self, fila: Dict[str, str]) -> Genero:
        """Obtiene la entidad a partir de una fila del CSV.

        Args:
            fila (Dict[str, str]): Fila leída del CSV.

        Returns:
            Genero: La entidad obtenida.
        """
        return Genero(int(fila["id"]), fila["nombre"], fila["descripcion"])

    def _copiar(self, destino: Genero, origen: Genero) -> None:
        """Copia los datos de `origen` en `destino`.

        Args:
            destino (Genero): Entidad guardada que se modifica.
            origen (Genero): Entidad con los datos nuevos.
        """
        destino.nombre = origen.nombre
        destino.descripcion = origen.descripcion


class RepositorioEditorial(RepositorioCSV[Editorial]):
    """Repositorio CSV de editoriales."""

    ARCHIVO = "editoriales.csv"
    CAMPOS = ["id", "nombre", "pais", "email", "estado"]

    def _a_fila(self, entidad: Editorial) -> Dict[str, object]:
        """Convierte la entidad en una fila del CSV.

        Args:
            entidad (Editorial): Entidad a procesar.

        Returns:
            Dict[str, object]: Diccionario con las columnas del CSV.
        """
        return {
            "id": entidad.id,
            "nombre": entidad.nombre,
            "pais": entidad.pais,
            "email": entidad.email,
        }

    def _desde_fila(self, fila: Dict[str, str]) -> Editorial:
        """Obtiene la entidad a partir de una fila del CSV.

        Args:
            fila (Dict[str, str]): Fila leída del CSV.

        Returns:
            Editorial: La entidad obtenida.
        """
        return Editorial(
            int(fila["id"]), fila["nombre"], fila["pais"], fila["email"]
        )

    def _copiar(self, destino: Editorial, origen: Editorial) -> None:
        """Copia los datos de `origen` en `destino`.

        Args:
            destino (Editorial): Entidad guardada que se modifica.
            origen (Editorial): Entidad con los datos nuevos.
        """
        destino.nombre = origen.nombre
        destino.pais = origen.pais
        destino.email = origen.email


class RepositorioMoneda(RepositorioCSV[Moneda]):
    """Repositorio CSV de monedas."""

    ARCHIVO = "monedas.csv"
    CAMPOS = [
        "id", "codigo", "nombre", "simbolo", "equivalencia_usd", "estado"
    ]

    def _a_fila(self, entidad: Moneda) -> Dict[str, object]:
        """Convierte la entidad en una fila del CSV.

        Args:
            entidad (Moneda): Entidad a procesar.

        Returns:
            Dict[str, object]: Diccionario con las columnas del CSV.
        """
        return {
            "id": entidad.id,
            "codigo": entidad.codigo,
            "nombre": entidad.nombre,
            "simbolo": entidad.simbolo,
            "equivalencia_usd": entidad.equivalencia_usd,
        }

    def _desde_fila(self, fila: Dict[str, str]) -> Moneda:
        """Obtiene la entidad a partir de una fila del CSV.

        Args:
            fila (Dict[str, str]): Fila leída del CSV.

        Returns:
            Moneda: La entidad obtenida.
        """
        return Moneda(
            int(fila["id"]),
            fila["codigo"],
            fila["nombre"],
            fila["simbolo"],
            float(fila["equivalencia_usd"]),
        )

    def _copiar(self, destino: Moneda, origen: Moneda) -> None:
        """Copia los datos de `origen` en `destino`.

        Args:
            destino (Moneda): Entidad guardada que se modifica.
            origen (Moneda): Entidad con los datos nuevos.
        """
        destino.codigo = origen.codigo
        destino.nombre = origen.nombre
        destino.simbolo = origen.simbolo
        destino.equivalencia_usd = origen.equivalencia_usd


class RepositorioTipoCotizacion(RepositorioCSV[TipoCotizacion]):
    """Repositorio CSV de tipos de cotización."""

    ARCHIVO = "tipos_cotizacion.csv"
    CAMPOS = ["id", "nombre", "descripcion", "estado"]

    def _a_fila(self, entidad: TipoCotizacion) -> Dict[str, object]:
        """Convierte la entidad en una fila del CSV.

        Args:
            entidad (TipoCotizacion): Entidad a procesar.

        Returns:
            Dict[str, object]: Diccionario con las columnas del CSV.
        """
        return {
            "id": entidad.id,
            "nombre": entidad.nombre,
            "descripcion": entidad.descripcion,
        }

    def _desde_fila(self, fila: Dict[str, str]) -> TipoCotizacion:
        """Obtiene la entidad a partir de una fila del CSV.

        Args:
            fila (Dict[str, str]): Fila leída del CSV.

        Returns:
            TipoCotizacion: La entidad obtenida.
        """
        return TipoCotizacion(
            int(fila["id"]), fila["nombre"], fila["descripcion"]
        )

    def _copiar(
        self, destino: TipoCotizacion, origen: TipoCotizacion
    ) -> None:
        """Copia los datos de `origen` en `destino`.

        Args:
            destino (TipoCotizacion): Entidad guardada que se modifica.
            origen (TipoCotizacion): Entidad con los datos nuevos.
        """
        destino.nombre = origen.nombre
        destino.descripcion = origen.descripcion


class RepositorioLibro(RepositorioCSV[Libro]):
    """Repositorio CSV de libros resuelve género y editorial por ID."""

    ARCHIVO = "libros.csv"
    CAMPOS = [
        "id", "isbn", "titulo", "autor", "anio", "genero_id",
        "editorial_id", "estado",
    ]

    def __init__(
        self,
        repo_genero: RepositorioGenero,
        repo_editorial: RepositorioEditorial,
        directorio: str = CSV_DIR,
    ) -> None:
        """Constructor.

        Args:
            repo_genero (RepositorioGenero): Repositorio de géneros.
            repo_editorial (RepositorioEditorial): Repositorio de editoriales.
            directorio (str): Carpeta donde se guardan los CSV.
        """
        self.__repo_genero: RepositorioGenero = repo_genero
        self.__repo_editorial: RepositorioEditorial = repo_editorial
        super().__init__(directorio)

    def leer_por_isbn(self, isbn: str) -> Optional[Libro]:
        """Busca un libro por ISBN (con o sin guiones).

        Args:
            isbn (str): ISBN de 10 o 13 caracteres.

        Returns:
            Optional[Libro]: El libro si existe, None en caso contrario.
        """
        isbn = isbn.replace("-", "").replace(" ", "").upper()
        return next(
            (libro for libro in self.leer_todos() if libro.isbn == isbn),
            None,
        )

    def _a_fila(self, entidad: Libro) -> Dict[str, object]:
        """Convierte la entidad en una fila del CSV.

        Args:
            entidad (Libro): Entidad a procesar.

        Returns:
            Dict[str, object]: Diccionario con las columnas del CSV.
        """
        return {
            "id": entidad.id,
            "isbn": entidad.isbn,
            "titulo": entidad.titulo,
            "autor": entidad.autor,
            "anio": entidad.anio,
            "genero_id": entidad.genero.id,
            "editorial_id": entidad.editorial.id,
        }

    def _desde_fila(self, fila: Dict[str, str]) -> Libro:
        """Obtiene la entidad a partir de una fila del CSV.

        Args:
            fila (Dict[str, str]): Fila leída del CSV.

        Returns:
            Libro: La entidad obtenida.
        """
        return Libro(
            int(fila["id"]),
            fila["isbn"],
            fila["titulo"],
            fila["autor"],
            int(fila["anio"]),
            _resolver(self.__repo_genero, int(fila["genero_id"]), "Género"),
            _resolver(
                self.__repo_editorial, int(fila["editorial_id"]), "Editorial"
            ),
        )

    def _copiar(self, destino: Libro, origen: Libro) -> None:
        """Copia los datos de `origen` en `destino`.

        Args:
            destino (Libro): Entidad guardada que se modifica.
            origen (Libro): Entidad con los datos nuevos.
        """
        destino.isbn = origen.isbn
        destino.titulo = origen.titulo
        destino.autor = origen.autor
        destino.anio = origen.anio
        destino.genero = origen.genero
        destino.editorial = origen.editorial


class RepositorioPrecio(RepositorioCSV[Precio]):
    """Repositorio CSV de precios resuelve libro y moneda por ID."""

    ARCHIVO = "precios.csv"
    CAMPOS = ["id", "libro_id", "moneda_id", "monto", "estado"]

    def __init__(
        self,
        repo_libro: RepositorioLibro,
        repo_moneda: RepositorioMoneda,
        directorio: str = CSV_DIR,
    ) -> None:
        """Constructor.

        Args:
            repo_libro (RepositorioLibro): Repositorio de libros.
            repo_moneda (RepositorioMoneda): Repositorio de monedas.
            directorio (str): Carpeta donde se guardan los CSV.
        """
        self.__repo_libro: RepositorioLibro = repo_libro
        self.__repo_moneda: RepositorioMoneda = repo_moneda
        super().__init__(directorio)

    def leer_por_libro(self, libro_id: int) -> List[Precio]:
        """Devuelve los precios de un libro.

        Args:
            libro_id (int): ID del libro.

        Returns:
            List[Precio]: Lista de precios del libro.
        """
        return [p for p in self.leer_todos() if p.libro.id == libro_id]

    def leer_por_moneda(self, moneda_id: int) -> List[Precio]:
        """Devuelve los precios expresados en una moneda.

        Args:
            moneda_id (int): ID de la moneda.

        Returns:
            List[Precio]: Lista de precios en esa moneda.
        """
        return [p for p in self.leer_todos() if p.moneda.id == moneda_id]

    def _a_fila(self, entidad: Precio) -> Dict[str, object]:
        """Convierte la entidad en una fila del CSV.

        Args:
            entidad (Precio): Entidad a procesar.

        Returns:
            Dict[str, object]: Diccionario con las columnas del CSV.
        """
        return {
            "id": entidad.id,
            "libro_id": entidad.libro.id,
            "moneda_id": entidad.moneda.id,
            "monto": entidad.monto,
        }

    def _desde_fila(self, fila: Dict[str, str]) -> Precio:
        """Obtiene la entidad a partir de una fila del CSV.

        Args:
            fila (Dict[str, str]): Fila leída del CSV.

        Returns:
            Precio: La entidad obtenida.
        """
        return Precio(
            int(fila["id"]),
            _resolver(self.__repo_libro, int(fila["libro_id"]), "Libro"),
            _resolver(self.__repo_moneda, int(fila["moneda_id"]), "Moneda"),
            float(fila["monto"]),
        )

    def _copiar(self, destino: Precio, origen: Precio) -> None:
        """Copia los datos de `origen` en `destino`.

        Args:
            destino (Precio): Entidad guardada que se modifica.
            origen (Precio): Entidad con los datos nuevos.
        """
        destino.libro = origen.libro
        destino.moneda = origen.moneda
        destino.monto = origen.monto


class RepositorioStock(IRepositorioStock):
    """Repositorio CSV de stock, identificado por el ID del libro.

    El borrado es lógico (columna `estado`), igual que en RepositorioCSV.
    """

    ARCHIVO = "stock.csv"
    CAMPOS = ["libro_id", "cantidad", "stock_minimo", "estado"]

    def __init__(
        self, repo_libro: RepositorioLibro, directorio: str = CSV_DIR
    ) -> None:
        """Constructor.

        Args:
            repo_libro (RepositorioLibro): Repositorio de libros.
            directorio (str): Carpeta donde se guardan los CSV.
        """
        self.__repo_libro: RepositorioLibro = repo_libro
        self.__archivo: ArchivoCSV = ArchivoCSV(
            self.ARCHIVO, self.CAMPOS, directorio
        )
        self.__stocks: Dict[int, Stock] = {}
        self.__estados: Dict[int, int] = {}
        for fila in self.__archivo.leer():
            stock = Stock(
                _resolver(repo_libro, int(fila["libro_id"]), "Libro"),
                int(fila["cantidad"]),
                int(fila["stock_minimo"]),
            )
            self.__stocks[stock.libro_id] = stock
            self.__estados[stock.libro_id] = _leer_estado(fila)

    def _guardar(self) -> None:
        """Se almacena todo el stock en el archivo, con su estado."""
        self.__archivo.escribir([
            {
                "libro_id": clave,
                "cantidad": self.__stocks[clave].cantidad,
                "stock_minimo": self.__stocks[clave].stock_minimo,
                "estado": self.__estados[clave],
            }
            for clave in sorted(self.__stocks)
        ])

    def _esta_activo(self, libro_id: int) -> bool:
        """Indica si hay stock activo para ese libro.

        Args:
            libro_id (int): ID del libro.

        Returns:
            bool: True si existe y no está borrado.
        """
        return self.__estados.get(libro_id) == ACTIVO

    def crear(self, stock: Stock) -> Stock:
        """Crea un nuevo registro en el repositorio.

        Si había un registro borrado para ese libro, se reactiva con los
        datos nuevos.

        Args:
            stock (Stock): Registro de stock.

        Returns:
            Stock: La entidad creada.

        Raises:
            ValueError: Si ya existe stock activo para ese libro.
        """
        if self._esta_activo(stock.libro_id):
            raise ValueError(
                f"Ya existe stock para el libro {stock.libro_id}."
            )
        self.__stocks[stock.libro_id] = stock
        self.__estados[stock.libro_id] = ACTIVO
        self._guardar()
        return stock

    def leer_por_libro(self, libro_id: int) -> Optional[Stock]:
        """Lee el stock activo de un libro.

        Args:
            libro_id (int): ID del libro.

        Returns:
            Optional[Stock]: El stock si existe y está activo, None en caso
                contrario.
        """
        if not self._esta_activo(libro_id):
            return None
        return self.__stocks[libro_id]

    def leer_todos(self) -> List[Stock]:
        """Devuelve los registros de stock activos ordenados por libro.

        Returns:
            List[Stock]: Lista de registros de stock ordenados por libro.
        """
        return [
            self.__stocks[clave]
            for clave in sorted(self.__stocks)
            if self._esta_activo(clave)
        ]

    def actualizar(self, stock: Stock) -> Stock:
        """Actualiza un registro existente.

        Args:
            stock (Stock): Registro de stock.

        Returns:
            Stock: La entidad actualizada.

        Raises:
            ValueError: Si no existe stock activo para ese libro.
        """
        if not self._esta_activo(stock.libro_id):
            raise ValueError(
                f"No existe stock para el libro {stock.libro_id}."
            )
        self.__stocks[stock.libro_id] = stock
        self._guardar()
        return stock

    def eliminar(self, libro_id: int) -> bool:
        """Borra lógicamente un registro (estado = 0).

        Args:
            libro_id (int): ID del libro.

        Returns:
            bool: True si se borró, False si no existía o ya estaba
                borrado.
        """
        if not self._esta_activo(libro_id):
            return False
        self.__estados[libro_id] = BORRADO
        self._guardar()
        return True


class RepositorioCotizacionDolar(IRepositorioCotizacionDolar):
    """Repositorio CSV de cotizaciones, identificadas por tipo y fecha.

    El borrado es lógico (columna `estado`), igual que en RepositorioCSV.
    """

    ARCHIVO = "cotizaciones_dolar.csv"
    CAMPOS = ["tipo_id", "fecha", "compra", "venta", "estado"]

    def __init__(
        self,
        repo_tipo: RepositorioTipoCotizacion,
        directorio: str = CSV_DIR,
    ) -> None:
        """Constructor.

        Args:
            repo_tipo (RepositorioTipoCotizacion): Repositorio de tipos de
                cotización.
            directorio (str): Carpeta donde se guardan los CSV.
        """
        self.__archivo: ArchivoCSV = ArchivoCSV(
            self.ARCHIVO, self.CAMPOS, directorio
        )
        self.__cotizaciones: Dict[Tuple[int, datetime.date], CotizacionDolar]
        self.__cotizaciones = {}
        self.__estados: Dict[Tuple[int, datetime.date], int] = {}
        for fila in self.__archivo.leer():
            cotizacion = CotizacionDolar(
                _resolver(repo_tipo, int(fila["tipo_id"]), "Tipo"),
                texto_a_fecha(fila["fecha"]),
                float(fila["compra"]),
                float(fila["venta"]),
            )
            self.__cotizaciones[self._clave(cotizacion)] = cotizacion
            self.__estados[self._clave(cotizacion)] = _leer_estado(fila)

    @staticmethod
    def _clave(
        cotizacion: CotizacionDolar,
    ) -> Tuple[int, datetime.date]:
        """Clave compuesta (tipo, fecha) de una cotización.

        Args:
            cotizacion (CotizacionDolar): Cotización del dólar.

        Returns:
            Tuple[int, datetime.date]: Tupla (tipo_id, fecha).
        """
        return cotizacion.tipo_id, cotizacion.fecha

    def _guardar(self) -> None:
        """Almacena todas las cotizaciones en el archivo, con su estado."""
        self.__archivo.escribir([
            {
                "tipo_id": c.tipo_id,
                "fecha": str(c.fecha),
                "compra": c.compra,
                "venta": c.venta,
                "estado": self.__estados[self._clave(c)],
            }
            for c in self._ordenadas(self.__cotizaciones.values())
        ])

    @staticmethod
    def _ordenadas(
        cotizaciones: Iterable[CotizacionDolar],
    ) -> List[CotizacionDolar]:
        """Ordena cotizaciones por fecha y tipo.

        Args:
            cotizaciones (Iterable[CotizacionDolar]): Cotizaciones a
                ordenar.

        Returns:
            List[CotizacionDolar]: Cotizaciones ordenadas por fecha y tipo.
        """
        return sorted(cotizaciones, key=lambda c: (c.fecha, c.tipo_id))

    def _esta_activa(self, clave: Tuple[int, datetime.date]) -> bool:
        """Indica si hay una cotización activa con esa clave.

        Args:
            clave (Tuple[int, datetime.date]): Tupla (tipo_id, fecha).

        Returns:
            bool: True si existe y no está borrada.
        """
        return self.__estados.get(clave) == ACTIVO

    def crear(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Crea un nuevo registro en el repositorio.

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
        clave = self._clave(cotizacion)
        if self._esta_activa(clave):
            raise ValueError(
                "Ya existe una cotización para ese tipo y fecha."
            )
        self.__cotizaciones[clave] = cotizacion
        self.__estados[clave] = ACTIVO
        self._guardar()
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
        if not self._esta_activa((tipo_id, fecha)):
            return None
        return self.__cotizaciones[(tipo_id, fecha)]

    def leer_historico_por_tipo(self, tipo_id: int) -> List[CotizacionDolar]:
        """Lee el histórico de cotizaciones de un tipo.

        Args:
            tipo_id (int): ID del tipo de cotización.

        Returns:
            List[CotizacionDolar]: Cotizaciones del tipo indicado.
        """
        return [c for c in self.leer_todos() if c.tipo_id == tipo_id]

    def leer_todos(self) -> List[CotizacionDolar]:
        """Devuelve las cotizaciones activas ordenadas por fecha y tipo.

        Returns:
            List[CotizacionDolar]: Cotizaciones ordenadas por fecha y tipo.
        """
        return self._ordenadas(
            c for c in self.__cotizaciones.values()
            if self._esta_activa(self._clave(c))
        )

    def actualizar(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Actualiza un registro existente.

        Args:
            cotizacion (CotizacionDolar): Cotización del dólar.

        Returns:
            CotizacionDolar: La entidad actualizada.

        Raises:
            ValueError: Si no existe la cotización activa.
        """
        if not self._esta_activa(self._clave(cotizacion)):
            raise ValueError(
                "No existe una cotización para ese tipo y fecha."
            )
        self.__cotizaciones[self._clave(cotizacion)] = cotizacion
        self._guardar()
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
        if not self._esta_activa((tipo_id, fecha)):
            return False
        self.__estados[(tipo_id, fecha)] = BORRADO
        self._guardar()
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


def crear_repositorios(directorio: str = CSV_DIR) -> Repositorios:
    """Instancia los repositorios respetando sus dependencias.

    Args:
        directorio (str): Carpeta donde se guardan los CSV.

    Returns:
        Repositorios: Los repositorios del sistema.
    """
    generos = RepositorioGenero(directorio)
    editoriales = RepositorioEditorial(directorio)
    monedas = RepositorioMoneda(directorio)
    tipos = RepositorioTipoCotizacion(directorio)
    libros = RepositorioLibro(generos, editoriales, directorio)
    return Repositorios(
        generos=generos,
        editoriales=editoriales,
        monedas=monedas,
        tipos_cotizacion=tipos,
        libros=libros,
        precios=RepositorioPrecio(libros, monedas, directorio),
        stock=RepositorioStock(libros, directorio),
        cotizaciones=RepositorioCotizacionDolar(tipos, directorio),
    )


def vaciar_archivos(directorio: str = CSV_DIR) -> None:
    """Deja todos los archivos CSV del sistema solo con su encabezado.

    Args:
        directorio (str): Carpeta donde se guardan los CSV.
    """
    for repositorio in (
        RepositorioGenero,
        RepositorioEditorial,
        RepositorioMoneda,
        RepositorioTipoCotizacion,
        RepositorioLibro,
        RepositorioPrecio,
        RepositorioStock,
        RepositorioCotizacionDolar,
    ):
        archivo = ArchivoCSV(
            repositorio.ARCHIVO, repositorio.CAMPOS, directorio
        )
        archivo.escribir([])
