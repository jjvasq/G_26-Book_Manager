"""Interfaz de consola (CLI) de Book Manager."""

from __future__ import annotations

import datetime
from typing import Callable, Iterable, List, Optional, Tuple, TypeVar

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
from book_manager.services.services import ServicioCRUD, Servicios

Accion = Callable[[], None]
V = TypeVar("V")


class OperacionCancelada(Exception):
    """Se lanza cuando el usuario cancela una operación con Enter."""


class Consola:
    """Menús de consola que operan los CRUD y reportes del sistema."""

    def __init__(self, servicios: Servicios) -> None:
        """Constructor.

        Args:
            servicios (Servicios): Servicios del sistema.
        """
        self.__servicios: Servicios = servicios

    def ejecutar(self) -> None:
        """Muestra el menú principal hasta que el usuario elige salir."""
        try:
            self._menu_principal()
        except (EOFError, KeyboardInterrupt):
            print()
        print("Sesión finalizada. ¡Nos vemos en la próxima lectura!")

    def _menu_principal(self) -> None:
        """Menú principal del sistema."""
        self._menu("LIBRERÍA G26 · Gestión de catálogo y depósito", [
            ("Catálogo de libros", self._menu_libros),
            ("Géneros literarios", self._menu_generos),
            ("Casas editoriales", self._menu_editoriales),
            ("Monedas", self._menu_monedas),
            ("Tipos de dólar", self._menu_tipos),
            ("Lista de precios", self._menu_precios),
            ("Depósito (stock)", self._menu_stock),
            ("Valor del dólar", self._menu_cotizaciones),
            ("Informes", self._menu_reportes),
        ], salir="Cerrar el programa")

    def _menu(
        self,
        titulo: str,
        opciones: List[Tuple[str, Accion]],
        salir: str = "Regresar",
    ) -> None:
        """Muestra un menú numerado y ejecuta la opción elegida.

        Args:
            titulo (str): Título del menú.
            opciones (List[Tuple[str, Accion]]): Lista de pares (texto,
                acción).
            salir (str): Texto de la opción 0.
        """
        while True:
            borde = "+" + "-" * (len(titulo) + 4) + "+"
            print(f"\n{borde}\n|  {titulo}  |\n{borde}")
            for numero, (texto, _) in enumerate(opciones, start=1):
                print(f"  [{numero}] {texto}")
            print(f"  [0] {salir}")
            eleccion = input("» Elija un número: ").strip()
            if eleccion == "0":
                return
            if not eleccion.isdigit() or not (
                1 <= int(eleccion) <= len(opciones)
            ):
                print("Ese número no está en el menú, pruebe otra vez.")
                continue
            try:
                opciones[int(eleccion) - 1][1]()
            except OperacionCancelada:
                print("Se canceló la operación.")
            except ValueError as error:
                print(f"[!] {error}")
            except RuntimeError as error:
                print(f"[!] {error}")

    def _menu_crud(
        self,
        titulo: str,
        listar: Accion,
        alta: Accion,
        modificar: Accion,
        baja: Accion,
        extras: Optional[List[Tuple[str, Accion]]] = None,
    ) -> None:
        """Menú estándar de CRUD con opciones adicionales opcionales.

        Args:
            titulo (str): Título del menú.
            listar (Accion): Acción de listado.
            alta (Accion): Acción de alta.
            modificar (Accion): Acción de modificación.
            baja (Accion): Acción de baja.
            extras (Optional[List[Tuple[str, Accion]]]): Opciones adicionales
                del menú.
        """
        self._menu(titulo, [
            ("Ver todos", listar),
            ("Agregar nuevo", alta),
            ("Editar existente", modificar),
            ("Eliminar", baja),
            *(extras or []),
        ])

    @staticmethod
    def _mostrar(
        items: Iterable[object], vacio: str = "(no hay registros cargados)"
    ) -> None:
        """Imprime una lista de objetos, uno por línea.

        Args:
            items (Iterable[object]): Objetos a mostrar.
            vacio (str): Mensaje si no hay registros.
        """
        items = list(items)
        for item in items:
            print(f"  {item}")
        if not items:
            print(f"  {vacio}")

    @staticmethod
    def _pedir_texto(mensaje: str, actual: Optional[str] = None) -> str:
        """Pide un texto; con Enter conserva el valor actual si lo hay.

        Args:
            mensaje (str): Texto a mostrar al usuario.
            actual (Optional[str]): Valor actual; con Enter se conserva.

        Returns:
            str: Texto ingresado.
        """
        sufijo = f" [{actual}]" if actual is not None else ""
        valor = input(f"{mensaje}{sufijo}: ").strip()
        return valor if valor or actual is None else actual

    @staticmethod
    def _pedir_entero(mensaje: str, actual: Optional[int] = None) -> int:
        """Pide un número entero hasta que sea válido.

        Args:
            mensaje (str): Texto a mostrar al usuario.
            actual (Optional[int]): Valor actual; con Enter se conserva.

        Returns:
            int: Número ingresado.
        """
        sufijo = f" [{actual}]" if actual is not None else ""
        while True:
            valor = input(f"{mensaje}{sufijo}: ").strip()
            if not valor and actual is not None:
                return actual
            try:
                return int(valor)
            except ValueError:
                print("Ingrese un número entero.")

    @classmethod
    def _pedir_id(cls, mensaje: str, actual: Optional[int] = None) -> int:
        """Pide un ID; con Enter conserva el actual o cancela la operación.

        Args:
            mensaje (str): Texto a mostrar al usuario.
            actual (Optional[int]): ID actual; con Enter se conserva.

        Returns:
            int: ID ingresado.

        Raises:
            OperacionCancelada: Si se deja vacío y no hay ID actual.
        """
        if actual is not None:
            return cls._pedir_entero(mensaje, actual)
        while True:
            valor = input(f"{mensaje} (Enter para cancelar): ").strip()
            if not valor:
                raise OperacionCancelada()
            try:
                return int(valor)
            except ValueError:
                print("Ingrese un número entero.")

    @staticmethod
    def _pedir_decimal(mensaje: str, actual: Optional[float] = None) -> float:
        """Pide un número decimal (acepta coma o punto).

        Args:
            mensaje (str): Texto a mostrar al usuario.
            actual (Optional[float]): Valor actual; con Enter se conserva.

        Returns:
            float: Número ingresado.
        """
        sufijo = f" [{actual:g}]" if actual is not None else ""
        while True:
            valor = input(f"{mensaje}{sufijo}: ").strip().replace(",", ".")
            if not valor and actual is not None:
                return actual
            try:
                return float(valor)
            except ValueError:
                print("Ingrese un número válido.")

    @staticmethod
    def _pedir_positivo_opcional(mensaje: str) -> Optional[float]:
        """Pide un número mayor a cero; con Enter devuelve None.

        Args:
            mensaje (str): Texto a mostrar al usuario.

        Returns:
            Optional[float]: Número ingresado, o None si se dejó vacío.
        """
        while True:
            valor = input(mensaje).strip().replace(",", ".")
            if not valor:
                return None
            try:
                numero = float(valor)
            except ValueError:
                print("Ingrese un número válido.")
                continue
            if numero <= 0:
                print("El valor debe ser mayor a cero.")
                continue
            return numero

    @classmethod
    def _pedir_cotizacion_manual(
        cls, tipo: TipoCotizacion
    ) -> Optional[Tuple[float, float]]:
        """Pide la cotización de un tipo cuando la API no responde.

        Args:
            tipo (TipoCotizacion): Tipo de cotización a cargar.

        Returns:
            Optional[Tuple[float, float]]: (compra, venta), o None si se
                saltea.
        """
        print(f"\nDólar {tipo.nombre} (Enter para saltear)")
        venta = cls._pedir_positivo_opcional("  Venta: ")
        if venta is None:
            return None
        compra = cls._pedir_positivo_opcional(
            "  Compra (Enter = igual a venta): "
        )
        return (compra or venta, venta)

    @staticmethod
    def _pedir_valido(
        pedir: Callable[[], V], *validaciones: Callable[[V], object]
    ) -> V:
        """Repite un pedido hasta que el valor ingresado sea válido.

        Args:
            pedir (Callable[[], V]): Función que pide el valor; puede
                lanzar ValueError si el valor no existe.
            *validaciones (Callable[[V], object]): Funciones que lanzan
                ValueError si el valor no es válido.

        Returns:
            V: El valor ingresado.
        """
        while True:
            try:
                valor = pedir()
                for validar in validaciones:
                    validar(valor)
                return valor
            except ValueError as error:
                print(f"[!] {error} Vuelva a ingresarlo.")

    def _pedir_atributo(
        self,
        clase: type,
        atributo: str,
        mensaje: str,
        actual: Optional[object] = None,
        pedir: Optional[Callable[[str, Optional[V]], V]] = None,
        validar: Optional[Callable[[V], object]] = None,
    ) -> V:
        """Pide un atributo de una entidad hasta que sea válido.

        El valor se valida con el setter de la propiedad sobre un objeto
        auxiliar, así las reglas quedan definidas solo en las entidades.

        Args:
            clase (type): Clase de la entidad.
            atributo (str): Nombre de la propiedad a pedir.
            mensaje (str): Texto a mostrar al usuario.
            actual (Optional[object]): Entidad actual; con Enter se
                conserva su valor.
            pedir (Optional[Callable[[str, Optional[V]], V]]): Función
                que pide el valor (por defecto, un texto).
            validar (Optional[Callable[[V], object]]): Validación
                adicional, por ejemplo de valores repetidos.

        Returns:
            V: El valor ingresado.
        """
        pedir = pedir or self._pedir_texto
        valor_actual = (
            getattr(actual, atributo) if actual is not None else None
        )
        setter = getattr(clase, atributo).fset
        validaciones = [lambda valor: setter(object.__new__(clase), valor)]
        if validar is not None:
            validaciones.append(validar)
        return self._pedir_valido(
            lambda: pedir(mensaje, valor_actual), *validaciones
        )

    @staticmethod
    def _pedir_fecha(
        mensaje: str, actual: Optional[datetime.date] = None
    ) -> datetime.date:
        """Pide una fecha AAAA-MM-DD; con Enter usa la actual o hoy.

        Args:
            mensaje (str): Texto a mostrar al usuario.
            actual (Optional[datetime.date]): Fecha actual; con Enter se
                conserva (por defecto, hoy).

        Returns:
            datetime.date: Fecha ingresada.
        """
        por_defecto = actual or datetime.date.today()
        while True:
            valor = input(f"{mensaje} [{por_defecto}]: ").strip()
            if not valor:
                return por_defecto
            try:
                return texto_a_fecha(valor)
            except ValueError:
                print("Formato inválido, use AAAA-MM-DD.")

    @staticmethod
    def _confirmar(mensaje: str) -> bool:
        """Pide confirmación s/n y avisa si la operación se cancela.

        Args:
            mensaje (str): Texto a mostrar al usuario.

        Returns:
            bool: True si el usuario respondió "s", "si" o "sí".
        """
        respuesta = input(f"{mensaje} (s/n): ").strip().lower()
        if respuesta in ("s", "si", "sí"):
            return True
        print("Se canceló la operación.")
        return False

    def _elegir_libro(self, actual: Optional[Libro] = None) -> Libro:
        """Lista los libros y devuelve el elegido por ID.

        Args:
            actual (Optional[Libro]): Libro actual; con Enter se conserva.

        Returns:
            Libro: El libro elegido.
        """
        return self._elegir(self.__servicios.libros, "ID del libro", actual)

    def _elegir(
        self, servicio: ServicioCRUD[V], mensaje: str, actual: Optional[V]
    ) -> V:
        """Lista los registros y pide un ID hasta que exista.

        Args:
            servicio (ServicioCRUD[V]): Servicio de la entidad.
            mensaje (str): Texto a mostrar al usuario.
            actual (Optional[V]): Registro actual; con Enter se conserva.

        Returns:
            V: El registro elegido.
        """
        self._mostrar(servicio.listar())
        return self._pedir_valido(lambda: servicio.obtener(
            self._pedir_id(mensaje, actual.id if actual else None)
        ))

    def _elegir_genero(self, actual: Optional[Genero] = None) -> Genero:
        """Lista los géneros y devuelve el elegido por ID.

        Args:
            actual (Optional[Genero]): Género actual; con Enter se conserva.

        Returns:
            Genero: El género elegido.
        """
        return self._elegir(self.__servicios.generos, "ID del género", actual)

    def _elegir_editorial(
        self, actual: Optional[Editorial] = None
    ) -> Editorial:
        """Lista las editoriales y devuelve la elegida por ID.

        Args:
            actual (Optional[Editorial]): Editorial actual; con Enter se
                conserva.

        Returns:
            Editorial: La editorial elegida.
        """
        return self._elegir(
            self.__servicios.editoriales, "ID de la editorial", actual
        )

    def _elegir_moneda(self, actual: Optional[Moneda] = None) -> Moneda:
        """Lista las monedas y devuelve la elegida por ID.

        Args:
            actual (Optional[Moneda]): Moneda actual; con Enter se conserva.

        Returns:
            Moneda: La moneda elegida.
        """
        return self._elegir(
            self.__servicios.monedas, "ID de la moneda", actual
        )

    def _elegir_tipo(
        self, actual: Optional[TipoCotizacion] = None
    ) -> TipoCotizacion:
        """Lista los tipos de cotización y devuelve el elegido por ID.

        Args:
            actual (Optional[TipoCotizacion]): Tipo actual; con Enter se
                conserva.

        Returns:
            TipoCotizacion: El tipo de cotización elegido.
        """
        return self._elegir(
            self.__servicios.tipos_cotizacion, "ID del tipo de cotización",
            actual,
        )

    def _menu_libros(self) -> None:
        """CRUD de libros."""
        servicio = self.__servicios.libros

        def datos(actual: Optional[Libro] = None) -> Libro:
            id = actual.id if actual else 0
            return Libro(
                id,
                self._pedir_atributo(
                    Libro, "isbn", "ISBN", actual,
                    validar=lambda isbn: servicio.verificar_isbn(isbn, id),
                ),
                self._pedir_atributo(Libro, "titulo", "Título", actual),
                self._pedir_atributo(Libro, "autor", "Autor", actual),
                self._pedir_atributo(
                    Libro, "anio", "Año", actual, self._pedir_entero
                ),
                self._elegir_genero(actual.genero if actual else None),
                self._elegir_editorial(actual.editorial if actual else None),
            )

        def buscar() -> None:
            texto = self._pedir_texto("¿Qué desea buscar?")
            self._mostrar(servicio.buscar(texto))

        self._menu_crud(
            "Inicio › Catálogo de libros",
            lambda: self._mostrar(servicio.listar()),
            lambda: print(f"Registrado: {servicio.crear(datos())}"),
            lambda: self._modificacion(
                servicio.actualizar, self._elegir_libro, datos
            ),
            lambda: self._baja(
                servicio.eliminar, self._pedir_id("ID del libro"),
                "También se borrarán sus precios y su stock. ¿Seguimos?",
            ),
            [("Buscar (título, autor o ISBN)", buscar)],
        )

    def _menu_generos(self) -> None:
        """CRUD de géneros."""
        servicio = self.__servicios.generos

        def datos(actual: Optional[Genero] = None) -> Genero:
            id = actual.id if actual else 0
            return Genero(
                id,
                self._pedir_atributo(
                    Genero, "nombre", "Nombre", actual,
                    validar=lambda valor: servicio.verificar_nombre(valor, id),
                ),
                self._pedir_atributo(
                    Genero, "descripcion", "Descripción", actual
                ),
            )

        self._menu_crud(
            "Inicio › Géneros literarios",
            lambda: self._mostrar(servicio.listar()),
            lambda: print(f"Registrado: {servicio.crear(datos())}"),
            lambda: self._modificacion(
                servicio.actualizar, self._elegir_genero, datos
            ),
            lambda: self._baja(
                servicio.eliminar, self._pedir_id("ID del género")
            ),
        )

    def _menu_editoriales(self) -> None:
        """CRUD de editoriales."""
        servicio = self.__servicios.editoriales

        def datos(actual: Optional[Editorial] = None) -> Editorial:
            id = actual.id if actual else 0
            return Editorial(
                id,
                self._pedir_atributo(
                    Editorial, "nombre", "Nombre", actual,
                    validar=lambda valor: servicio.verificar_nombre(valor, id),
                ),
                self._pedir_atributo(Editorial, "pais", "País", actual),
                self._pedir_atributo(Editorial, "email", "Email", actual),
            )

        self._menu_crud(
            "Inicio › Casas editoriales",
            lambda: self._mostrar(servicio.listar()),
            lambda: print(f"Registrada: {servicio.crear(datos())}"),
            lambda: self._modificacion(
                servicio.actualizar, self._elegir_editorial, datos
            ),
            lambda: self._baja(
                servicio.eliminar, self._pedir_id("ID de la editorial")
            ),
        )

    def _menu_monedas(self) -> None:
        """CRUD de monedas."""
        servicio = self.__servicios.monedas

        def datos(actual: Optional[Moneda] = None) -> Moneda:
            id = actual.id if actual else 0
            return Moneda(
                id,
                self._pedir_atributo(
                    Moneda, "codigo", "Código (3 letras)", actual,
                    validar=lambda valor: servicio.verificar_codigo(valor, id),
                ),
                self._pedir_atributo(Moneda, "nombre", "Nombre", actual),
                self._pedir_atributo(Moneda, "simbolo", "Símbolo", actual),
                self._pedir_atributo(
                    Moneda, "equivalencia_usd",
                    "Equivalencia en USD de 1 unidad", actual,
                    self._pedir_decimal,
                ),
            )

        self._menu_crud(
            "Inicio › Monedas",
            lambda: self._mostrar(servicio.listar()),
            lambda: print(f"Registrada: {servicio.crear(datos())}"),
            lambda: self._modificacion(
                servicio.actualizar, self._elegir_moneda, datos
            ),
            lambda: self._baja(
                servicio.eliminar, self._pedir_id("ID de la moneda")
            ),
        )

    def _menu_tipos(self) -> None:
        """CRUD de tipos de cotización."""
        servicio = self.__servicios.tipos_cotizacion

        def datos(actual: Optional[TipoCotizacion] = None) -> TipoCotizacion:
            id = actual.id if actual else 0
            return TipoCotizacion(
                id,
                self._pedir_atributo(
                    TipoCotizacion, "nombre", "Nombre", actual,
                    validar=lambda valor: servicio.verificar_nombre(valor, id),
                ),
                self._pedir_atributo(
                    TipoCotizacion, "descripcion", "Descripción", actual
                ),
            )

        self._menu_crud(
            "Inicio › Tipos de dólar",
            lambda: self._mostrar(servicio.listar()),
            lambda: print(f"Registrado: {servicio.crear(datos())}"),
            lambda: self._modificacion(
                servicio.actualizar, self._elegir_tipo, datos
            ),
            lambda: self._baja(
                servicio.eliminar, self._pedir_id("ID del tipo")
            ),
        )

    def _menu_precios(self) -> None:
        """CRUD de precios."""
        servicio = self.__servicios.precios

        def datos(actual: Optional[Precio] = None) -> Precio:
            id = actual.id if actual else 0
            libro = self._elegir_libro(actual.libro if actual else None)
            moneda = self._pedir_valido(
                lambda: self._elegir_moneda(actual.moneda if actual else None),
                lambda moneda: servicio.verificar_moneda(
                    libro.id, moneda.id, id
                ),
            )
            monto = self._pedir_atributo(
                Precio, "monto", "Monto", actual, self._pedir_decimal
            )
            return Precio(id, libro, moneda, monto)

        def por_libro() -> None:
            libro = self._elegir_libro()
            self._mostrar(servicio.listar_por_libro(libro.id))

        self._menu_crud(
            "Inicio › Lista de precios",
            lambda: self._mostrar(servicio.listar()),
            lambda: print(f"Registrado: {servicio.crear(datos())}"),
            lambda: self._modificacion(
                servicio.actualizar,
                lambda: self._elegir(servicio, "ID del precio", None),
                datos,
            ),
            lambda: self._baja(
                servicio.eliminar, self._pedir_id("ID del precio")
            ),
            [("Ver los precios de un libro", por_libro)],
        )

    def _menu_stock(self) -> None:
        """CRUD y movimientos de stock."""
        servicio = self.__servicios.stock

        def elegir_stock() -> Stock:
            self._mostrar(servicio.listar())
            return self._pedir_valido(
                lambda: servicio.obtener(self._pedir_id("ID del libro"))
            )

        def datos(libro: Libro, actual: Optional[Stock] = None) -> Stock:
            return Stock(
                libro,
                self._pedir_atributo(
                    Stock, "cantidad", "Cantidad", actual, self._pedir_entero
                ),
                self._pedir_atributo(
                    Stock, "stock_minimo", "Stock mínimo", actual,
                    self._pedir_entero,
                ),
            )

        def alta() -> None:
            libro = self._pedir_valido(
                self._elegir_libro,
                lambda libro: servicio.verificar_sin_stock(libro.id),
            )
            print(f"Registrado: {servicio.crear(datos(libro))}")

        def modificar() -> None:
            actual = elegir_stock()
            stock = datos(actual.libro, actual)
            print(f"Cambios guardados: {servicio.actualizar(stock)}")

        def movimiento(ingreso: bool) -> None:
            stock = elegir_stock()

            def simular(unidades: int) -> None:
                copia = Stock(stock.libro, stock.cantidad, stock.stock_minimo)
                (copia.ingresar if ingreso else copia.retirar)(unidades)

            unidades = self._pedir_valido(
                lambda: self._pedir_entero("Cantidad de ejemplares"), simular
            )
            operacion = servicio.ingresar if ingreso else servicio.retirar
            print(f"Stock resultante: {operacion(stock.libro_id, unidades)}")

        self._menu_crud(
            "Inicio › Depósito (stock)",
            lambda: self._mostrar(servicio.listar()),
            alta,
            modificar,
            lambda: self._baja(
                servicio.eliminar, self._pedir_id("ID del libro")
            ),
            [
                ("Entrada de ejemplares", lambda: movimiento(True)),
                ("Salida / venta de ejemplares", lambda: movimiento(False)),
            ],
        )

    def _menu_cotizaciones(self) -> None:
        """CRUD de cotizaciones del dólar."""
        servicio = self.__servicios.cotizaciones

        def valores(
            tipo: TipoCotizacion,
            fecha: datetime.date,
            actual: Optional[CotizacionDolar] = None,
        ) -> CotizacionDolar:
            return CotizacionDolar(
                tipo,
                fecha,
                self._pedir_atributo(
                    CotizacionDolar, "compra", "Compra", actual,
                    self._pedir_decimal,
                ),
                self._pedir_atributo(
                    CotizacionDolar, "venta", "Venta", actual,
                    self._pedir_decimal,
                ),
            )

        def elegir_cotizacion(tipo: TipoCotizacion) -> CotizacionDolar:
            return self._pedir_valido(
                lambda: servicio.obtener(tipo.id, self._pedir_fecha("Fecha"))
            )

        def alta() -> None:
            tipo = self._elegir_tipo()
            fecha = self._pedir_atributo(
                CotizacionDolar, "fecha", "Fecha", None, self._pedir_fecha,
                validar=lambda fecha: servicio.verificar_fecha(tipo.id, fecha),
            )
            print(f"Registrada: {servicio.crear(valores(tipo, fecha))}")

        def modificar() -> None:
            tipo = self._elegir_tipo()
            historico = servicio.historico(tipo.id)
            self._mostrar(historico)
            if not historico:
                print("No hay cotizaciones para modificar.")
                return
            actual = elegir_cotizacion(tipo)
            cotizacion = valores(tipo, actual.fecha, actual)
            print(f"Cambios guardados: {servicio.actualizar(cotizacion)}")

        def baja() -> None:
            tipo = self._elegir_tipo()
            historico = servicio.historico(tipo.id)
            self._mostrar(historico)
            if not historico:
                print("No hay cotizaciones para eliminar.")
                return
            fecha = elegir_cotizacion(tipo).fecha
            if self._confirmar("¿Seguro que desea eliminarla?"):
                servicio.eliminar(tipo.id, fecha)
                print("Cotización eliminada.")

        def historico() -> None:
            self._mostrar(servicio.historico(self._elegir_tipo().id))

        def desde_api() -> None:
            print("Conectando con dolarapi.com ...")
            try:
                self._mostrar(servicio.actualizar_desde_api())
                return
            except RuntimeError:
                print(
                    "No se pudo consultar dolarapi.com; "
                    "cargue los valores a mano."
                )
            registradas = []
            for tipo in self.__servicios.tipos_cotizacion.listar():
                valores_manuales = self._pedir_cotizacion_manual(tipo)
                if valores_manuales is not None:
                    compra, venta = valores_manuales
                    registradas.append(
                        servicio.registrar_manual(tipo, compra, venta)
                    )
            self._mostrar(registradas)

        self._menu_crud(
            "Inicio › Valor del dólar",
            lambda: self._mostrar(servicio.listar()),
            alta,
            modificar,
            baja,
            [
                ("Historial de un tipo de dólar", historico),
                ("Traer cotizaciones del día (dolarapi.com)", desde_api),
            ],
        )

    def _aviso_cotizacion(self) -> None:
        """Informa si las cotizaciones usadas están en tiempo real."""
        cotizaciones = self.__servicios.cotizaciones
        if cotizaciones.en_tiempo_real and cotizaciones.ultima_consulta:
            hora = cotizaciones.ultima_consulta.strftime("%H:%M")
            print(f"\nCotización en tiempo real (dolarapi.com, {hora} hs).")
        else:
            print(
                "\nNo se pudo consultar dolarapi.com: se usa la última "
                "cotización guardada."
            )

    def _menu_reportes(self) -> None:
        """Reportes del sistema."""
        reportes = self.__servicios.reportes

        def inventario() -> None:
            tipo = self._elegir_tipo()
            print("Consultando cotización ...")
            detalle, total = reportes.valor_inventario(tipo.id)
            self._aviso_cotizacion()
            cotizacion = self.__servicios.cotizaciones.ultima(tipo.id)
            print(
                f"Inventario valorizado con dólar {tipo.nombre} "
                f"($ {cotizacion.venta:,.2f} del {cotizacion.fecha}):"
            )
            for stock, subtotal in detalle:
                print(
                    f"  {stock.libro.titulo:<40} {stock.cantidad:>4} u. "
                    f"$ {subtotal:>14,.2f}"
                )
            print(f"  {'TOTAL':<47} $ {total:>14,.2f}")

        def bajo_minimo() -> None:
            self._mostrar(
                self.__servicios.stock.bajo_minimo(),
                "Todos los libros superan su stock mínimo.",
            )

        def cotizar_libro() -> None:
            libro = self._elegir_libro()
            print("Consultando cotización ...")
            filas = reportes.cotizar_libro(libro.id)
            self._aviso_cotizacion()
            if not filas:
                print("  El libro no tiene precios en moneda extranjera.")
            for tipo, cotizacion, precio, pesos in filas:
                print(
                    f"  {precio.moneda.codigo} {precio.monto:,.2f} "
                    f"x {tipo.nombre:<10} ({cotizacion.fecha}) "
                    f"= $ {pesos:,.2f}"
                )

        self._menu("Inicio › Informes", [
            ("Inventario valorizado en pesos", inventario),
            ("Libros para reponer (bajo el mínimo)", bajo_minimo),
            ("Precio de un libro según cada dólar", cotizar_libro),
        ])

    @staticmethod
    def _modificacion(
        actualizar: Callable, elegir: Callable, datos: Callable
    ) -> None:
        """Elige un registro, pide los nuevos datos y lo actualiza.

        Args:
            actualizar (Callable): Método de actualización del servicio.
            elegir (Callable): Función que elige el registro a modificar.
            datos (Callable): Función que pide los datos al usuario.
        """
        print(f"Cambios guardados: {actualizar(datos(elegir()))}")

    def _baja(
        self,
        eliminar: Callable[[int], None],
        id: int,
        mensaje: str = "¿Seguro que desea eliminarlo?",
    ) -> None:
        """Pide confirmación y elimina el registro indicado.

        Args:
            eliminar (Callable[[int], None]): Método de baja del servicio.
            id (int): ID del registro a eliminar.
            mensaje (str): Texto a mostrar al usuario.
        """
        if self._confirmar(mensaje):
            eliminar(id)
            print("Registro eliminado.")
