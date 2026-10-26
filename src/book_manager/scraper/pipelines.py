"""Pipelines que procesan los items obtenidos de Cúspide."""

from __future__ import annotations

import json
from typing import IO, Dict, List, Optional, Set, Tuple

from itemadapter import ItemAdapter
from scrapy import Item, Spider
from scrapy.crawler import Crawler
from scrapy.exceptions import DropItem

from book_manager.scraper.settings import ARCHIVO_RESULTADOS

# Campos sin los que un resultado no sirve para comparar precios.
CAMPOS_OBLIGATORIOS = ("libro_id", "posicion", "titulo", "url", "precio")


class ValidarItemPipeline:
    """Descarta los items incompletos o con un precio inválido."""

    def process_item(
        self, item: Item, spider: Optional[Spider] = None
    ) -> Item:
        """Valida el item.

        Args:
            item (Item): Item obtenido por el spider.
            spider (Optional[Spider]): Spider que lo obtuvo (solo lo
                pasan las versiones de Scrapy anteriores a 2.14).

        Returns:
            Item: El mismo item, si es válido.

        Raises:
            DropItem: Si falta un campo obligatorio o el precio no es
                mayor a cero.
        """
        adaptador = ItemAdapter(item)
        faltantes = [c for c in CAMPOS_OBLIGATORIOS if not adaptador.get(c)]
        if faltantes:
            raise DropItem(
                f"Faltan datos ({', '.join(faltantes)}): "
                f"{adaptador.get('url')}"
            )
        if adaptador["precio"] <= 0:
            raise DropItem(f"Precio inválido: {adaptador['url']}")
        if not adaptador.get("descripcion"):
            adaptador["descripcion"] = "Sin descripción en el sitio."
        return item


class DuplicadosPipeline:
    """Descarta un producto repetido en la búsqueda de un mismo libro."""

    def __init__(self) -> None:
        """Constructor."""
        self.__vistos: Set[Tuple[int, str]] = set()

    def process_item(
        self, item: Item, spider: Optional[Spider] = None
    ) -> Item:
        """Verifica que el producto no se haya procesado para ese libro.

        Args:
            item (Item): Item obtenido por el spider.
            spider (Optional[Spider]): Spider que lo obtuvo.

        Returns:
            Item: El mismo item, si no está repetido.

        Raises:
            DropItem: Si el producto ya se procesó para ese libro.
        """
        adaptador = ItemAdapter(item)
        clave = (adaptador["libro_id"], adaptador["url"])
        if clave in self.__vistos:
            raise DropItem(f"Producto repetido: {adaptador['url']}")
        self.__vistos.add(clave)
        return item


class FormasDePagoPipeline:
    """Arma la lista de formas de pago con el precio de cada una.

    Para las compras en Argentina el precio es el precio en pesos; para
    las internacionales, el precio en dólares que informa el sitio.
    """

    @staticmethod
    def _forma(
        texto: str, alcance: str, moneda: str, precio: Optional[float]
    ) -> Dict[str, object]:
        """Arma una forma de pago separando el nombre de su detalle.

        Args:
            texto (str): Texto del medio de pago (ej.: "MercadoPago" o
                "Tarjetas de créditos: Visa y Mastercard.").
            alcance (str): "Argentina" o "Internacional".
            moneda (str): Código de la moneda del precio.
            precio (Optional[float]): Precio con esa forma de pago.

        Returns:
            Dict[str, object]: Forma de pago.
        """
        nombre, _, detalle = texto.partition(":")
        return {
            "forma": nombre.strip(),
            "detalle": detalle.strip(),
            "alcance": alcance,
            "moneda": moneda,
            "precio": precio,
        }

    def process_item(
        self, item: Item, spider: Optional[Spider] = None
    ) -> Item:
        """Reemplaza los medios de pago por las formas de pago y precio.

        Args:
            item (Item): Item obtenido por el spider.
            spider (Optional[Spider]): Spider que lo obtuvo.

        Returns:
            Item: El item con el campo `formas_pago`.
        """
        adaptador = ItemAdapter(item)
        formas: List[Dict[str, object]] = [
            self._forma(texto, "Argentina", "ARS", adaptador["precio"])
            for texto in adaptador.get("medios_pago_argentina") or []
        ]
        if adaptador.get("precio_usd"):
            formas += [
                self._forma(
                    texto, "Internacional", "USD", adaptador["precio_usd"]
                )
                for texto in adaptador.get("medios_pago_internacionales")
                or []
            ]
        adaptador["formas_pago"] = formas
        adaptador.pop("medios_pago_argentina", None)
        adaptador.pop("medios_pago_internacionales", None)
        return item


class GuardarResultadosPipeline:
    """Guarda cada item en un archivo JSON Lines (un item por línea).

    El archivo lo lee después el servicio de competencia, que registra los
    resultados en la base de datos.
    """

    def __init__(self, ruta: str) -> None:
        """Constructor.

        Args:
            ruta (str): Ruta del archivo de resultados.
        """
        self.__ruta: str = ruta
        self.__archivo: Optional[IO[str]] = None

    @classmethod
    def from_crawler(cls, crawler: Crawler) -> GuardarResultadosPipeline:
        """Crea el pipeline con la ruta de la configuración.

        Args:
            crawler (Crawler): Crawler en ejecución.

        Returns:
            GuardarResultadosPipeline: El pipeline.
        """
        return cls(crawler.settings.get(
            "ARCHIVO_RESULTADOS", ARCHIVO_RESULTADOS
        ))

    def open_spider(self, spider: Optional[Spider] = None) -> None:
        """Abre (vacío) el archivo de resultados.

        Args:
            spider (Optional[Spider]): Spider que se inicia.
        """
        self.__archivo = open(self.__ruta, "w", encoding="utf-8")

    def close_spider(self, spider: Optional[Spider] = None) -> None:
        """Cierra el archivo de resultados.

        Args:
            spider (Optional[Spider]): Spider que finaliza.
        """
        if self.__archivo is not None:
            self.__archivo.close()
            self.__archivo = None

    def process_item(
        self, item: Item, spider: Optional[Spider] = None
    ) -> Item:
        """Escribe el item en el archivo.

        Args:
            item (Item): Item procesado.
            spider (Optional[Spider]): Spider que lo obtuvo.

        Returns:
            Item: El mismo item.
        """
        if self.__archivo is not None:
            linea = json.dumps(ItemAdapter(item).asdict(), ensure_ascii=False)
            self.__archivo.write(linea + "\n")
            self.__archivo.flush()
        return item
