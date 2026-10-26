"""Spider que obtiene de Cúspide los datos de los libros del catálogo."""

from __future__ import annotations

import datetime
import json
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional
from urllib.parse import urlencode, urlparse

import scrapy
from scrapy.http import Response

from book_manager.scraper.loaders import LibroWebLoader

# Cantidad de resultados que se toman de cada búsqueda.
MAXIMO_RESULTADOS = 10


class CuspideSpider(scrapy.Spider):
    """Busca en Cúspide cada libro del catálogo por su título.

    De cada búsqueda toma los 10 primeros resultados y entra en la página
    de cada uno para obtener el precio, la URL de la imagen, las formas de
    pago con su precio y la descripción detallada. Solo se buscan los
    libros del catálogo, que se reciben en un archivo JSON.
    """

    name = "cuspide"
    url_base = "https://cuspide.com"
    allowed_domains = ["cuspide.com"]

    def __init__(
        self,
        catalogo: str = "",
        url_base: Optional[str] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Constructor.

        Args:
            catalogo (str): Ruta del archivo JSON con los libros del
                catálogo: lista de objetos con `id` y `titulo`.
            url_base (Optional[str]): URL del sitio (por defecto Cúspide).
            *args (Any): Argumentos de scrapy.Spider.
            **kwargs (Any): Argumentos con nombre de scrapy.Spider.

        Raises:
            ValueError: Si no se indica el archivo del catálogo.
        """
        super().__init__(*args, **kwargs)
        if not catalogo:
            raise ValueError("Falta el archivo del catálogo (-a catalogo=).")
        with open(catalogo, "r", encoding="utf-8") as archivo:
            self.libros: List[Dict[str, Any]] = json.load(archivo)
        if url_base:
            self.url_base = url_base.rstrip("/")
            self.allowed_domains = [urlparse(self.url_base).hostname or ""]

    def url_busqueda(self, titulo: str) -> str:
        """Arma la URL de búsqueda de productos por título.

        Args:
            titulo (str): Título a buscar.

        Returns:
            str: URL de la búsqueda.
        """
        consulta = urlencode({"s": titulo, "post_type": "product"})
        return f"{self.url_base}/?{consulta}"

    async def start(self) -> AsyncIterator[scrapy.Request]:
        """Genera una búsqueda por cada libro del catálogo.

        Yields:
            scrapy.Request: Solicitud de la búsqueda.
        """
        for libro in self.libros:
            yield scrapy.Request(
                self.url_busqueda(libro["titulo"]),
                callback=self.parse_busqueda,
                cb_kwargs={
                    "libro_id": libro["id"], "busqueda": libro["titulo"]
                },
                dont_filter=True,
            )

    def parse_busqueda(
        self, response: Response, libro_id: int, busqueda: str
    ) -> Iterator[Any]:
        """Procesa el listado de resultados de una búsqueda.

        Si el sitio redirige directamente a la ficha de un producto (un
        único resultado), se procesa esa ficha.

        Args:
            response (Response): Respuesta con los resultados.
            libro_id (int): ID del libro buscado.
            busqueda (str): Texto buscado.

        Yields:
            scrapy.Request | LibroWebItem: Solicitudes de las fichas de
                los productos o el item de la ficha.
        """
        if response.css("h1.product_title"):
            yield from self.parse_producto(response, libro_id, busqueda, 1)
            return
        resultados = response.css("div.products > div.product-small")
        if not resultados:
            self.logger.info("Sin resultados para '%s'.", busqueda)
        for posicion, resultado in enumerate(
            resultados[:MAXIMO_RESULTADOS], start=1
        ):
            enlace = resultado.css("p.product-title a::attr(href)").get()
            if enlace:
                yield response.follow(
                    enlace,
                    callback=self.parse_producto,
                    cb_kwargs={
                        "libro_id": libro_id,
                        "busqueda": busqueda,
                        "posicion": posicion,
                    },
                    dont_filter=True,
                )

    def parse_producto(
        self, response: Response, libro_id: int, busqueda: str, posicion: int
    ) -> Iterator[Any]:
        """Obtiene los datos de la ficha de un producto.

        Args:
            response (Response): Respuesta con la ficha del producto.
            libro_id (int): ID del libro buscado.
            busqueda (str): Texto buscado.
            posicion (int): Posición del producto en la búsqueda.

        Yields:
            LibroWebItem: Datos del producto.
        """
        loader = LibroWebLoader(response=response)
        loader.add_value("libro_id", libro_id)
        loader.add_value("busqueda", busqueda)
        loader.add_value("posicion", posicion)
        loader.add_value("url", response.url)
        loader.add_value(
            "fecha_extraccion",
            datetime.datetime.now().isoformat(timespec="seconds"),
        )
        loader.add_css("titulo", "h1.product_title::text")
        loader.add_css("autor", "h1.product_title + span a::text")
        loader.add_css("isbn", ".product_meta .sku::text")
        precio = response.css(".product-info p.price ins bdi") or response.css(
            ".product-info p.price bdi"
        )
        loader.add_value("precio", precio.xpath("string()").getall()[:1])
        loader.add_xpath(
            "precio_usd",
            "//div[contains(@class, 'product-info')]"
            "//span[starts-with(normalize-space(text()), 'U$s')]/span/text()",
        )
        loader.add_css(
            "url_imagen",
            ".woocommerce-product-gallery__image img::attr(data-large_image)",
        )
        loader.add_css(
            "url_imagen", ".woocommerce-product-gallery__image img::attr(src)"
        )
        loader.add_css(
            "url_imagen", "meta[property='og:image']::attr(content)"
        )
        loader.add_css(
            "medios_pago_argentina", "#contentPaymentsPopUpArg li::text"
        )
        loader.add_css(
            "medios_pago_internacionales", "#contentPaymentsPopUpInt li::text"
        )
        loader.add_xpath(
            "descripcion",
            "//div[contains(@class, 'product-section')]"
            "[.//h5[contains(., 'Descripci')]]"
            "//div[contains(@class, 'panel')]"
            "//p[not(contains(@class, 'livriz-hidden'))]//text()",
        )
        yield loader.load_item()
