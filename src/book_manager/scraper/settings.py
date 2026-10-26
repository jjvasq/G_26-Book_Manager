"""Configuración del proyecto Scrapy del Book Manager."""

BOT_NAME = "book_manager_scraper"

SPIDER_MODULES = ["book_manager.scraper.spiders"]
NEWSPIDER_MODULE = "book_manager.scraper.spiders"

# Identificación del scraper ante el sitio.
USER_AGENT = (
    "Mozilla/5.0 (compatible; BookManagerG26/1.0; "
    "+https://github.com/jjvasq/G_26-Book_Manager)"
)

# Se respeta el robots.txt del sitio y se limita la carga sobre el
# servidor: pocas solicitudes simultáneas y una demora entre cada una.
ROBOTSTXT_OBEY = True
CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 4
DOWNLOAD_DELAY = 0.5
DOWNLOAD_TIMEOUT = 30
RETRY_TIMES = 2
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 0.5
AUTOTHROTTLE_MAX_DELAY = 5
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0
COOKIES_ENABLED = False

DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "es-AR,es;q=0.9",
}

# Orden de los pipelines: primero se valida, luego se descartan los
# repetidos, se arman las formas de pago y por último se guarda.
ITEM_PIPELINES = {
    "book_manager.scraper.pipelines.ValidarItemPipeline": 100,
    "book_manager.scraper.pipelines.DuplicadosPipeline": 200,
    "book_manager.scraper.pipelines.FormasDePagoPipeline": 300,
    "book_manager.scraper.pipelines.GuardarResultadosPipeline": 400,
}

# Archivo JSON Lines donde GuardarResultadosPipeline escribe los items.
ARCHIVO_RESULTADOS = "resultados_cuspide.jsonl"

FEED_EXPORT_ENCODING = "utf-8"
LOG_LEVEL = "INFO"
