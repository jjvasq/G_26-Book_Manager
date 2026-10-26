"""Ejecuta el spider de Cúspide en un proceso propio.

Se usa desde el servicio de competencia con `python -m
book_manager.scraper.ejecutar`: así Scrapy (Twisted) corre en un proceso
nuevo cada vez y el scraping se puede repetir dentro del mismo notebook.
"""

from __future__ import annotations

import argparse
from typing import List, Optional

from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from book_manager.scraper import settings as configuracion
from book_manager.scraper.spiders.cuspide import CuspideSpider


def ejecutar_spider(
    catalogo: str, salida: str, url_base: Optional[str] = None
) -> None:
    """Ejecuta CuspideSpider y espera a que termine.

    Args:
        catalogo (str): Archivo JSON con los libros a buscar.
        salida (str): Archivo JSON Lines donde se guardan los resultados.
        url_base (Optional[str]): URL del sitio (por defecto Cúspide).
    """
    ajustes = Settings()
    ajustes.setmodule(configuracion)
    ajustes.set("ARCHIVO_RESULTADOS", salida)
    proceso = CrawlerProcess(ajustes)
    proceso.crawl(CuspideSpider, catalogo=catalogo, url_base=url_base)
    proceso.start()


def main(argumentos: Optional[List[str]] = None) -> None:
    """Lee los argumentos de la línea de comandos y ejecuta el spider.

    Args:
        argumentos (Optional[List[str]]): Argumentos (por defecto, los
            de la línea de comandos).
    """
    lector = argparse.ArgumentParser(description=__doc__)
    lector.add_argument("--catalogo", required=True)
    lector.add_argument("--salida", required=True)
    lector.add_argument("--url-base", default=None)
    opciones = lector.parse_args(argumentos)
    ejecutar_spider(opciones.catalogo, opciones.salida, opciones.url_base)


if __name__ == "__main__":
    main()
