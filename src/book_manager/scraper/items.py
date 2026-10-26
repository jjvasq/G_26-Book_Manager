"""Items que obtiene el scraper de Cúspide."""

import scrapy


class LibroWebItem(scrapy.Item):
    """Datos de un libro publicado en el sitio de un competidor.

    Cada item corresponde a uno de los resultados de la búsqueda de un
    libro del catálogo (`libro_id`) y guarda su posición en esa búsqueda.
    """

    libro_id = scrapy.Field()
    busqueda = scrapy.Field()
    posicion = scrapy.Field()
    titulo = scrapy.Field()
    autor = scrapy.Field()
    isbn = scrapy.Field()
    url = scrapy.Field()
    url_imagen = scrapy.Field()
    precio = scrapy.Field()
    precio_usd = scrapy.Field()
    medios_pago_argentina = scrapy.Field()
    medios_pago_internacionales = scrapy.Field()
    formas_pago = scrapy.Field()
    descripcion = scrapy.Field()
    fecha_extraccion = scrapy.Field()
