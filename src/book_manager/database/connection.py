"""Conexión a la base de datos con SQLAlchemy."""

from __future__ import annotations

import os
from typing import Optional, Union
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import Session, sessionmaker

# Carpeta raíz del proyecto, donde se encuentra el archivo .env.
RAIZ_PROYECTO = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
ARCHIVO_ENV = os.path.join(RAIZ_PROYECTO, ".env")

# Marcador que Supabase deja en la URL (Connect > ORM > DIRECT_URL) en el
# lugar de la contraseña.
MARCADOR_PASSWORD = "[YOUR-PASSWORD]"

# Driver con el que SQLAlchemy se conecta a PostgreSQL (psycopg2-binary en
# requirements.txt). Se fija explícitamente porque el driver por defecto de
# "postgresql://" puede cambiar según la versión de SQLAlchemy.
PREFIJO_URL = "postgresql://"
PREFIJO_DRIVER = "postgresql+psycopg2://"


def url_desde_entorno() -> str:
    """Arma la URL de conexión a Supabase con las variables de entorno.

    La URL (DATABASE_URL) se copia de Supabase > Connect > ORM >
    DIRECT_URL y se guarda en el archivo .env tal como la da Supabase,
    con el marcador [YOUR-PASSWORD]. La contraseña no se guarda en el
    repositorio: se lee de la variable SUPABASE_DB_PASSWORD (en Colab,
    desde los secrets) y reemplaza al marcador.

    Returns:
        str: URL de conexión completa.

    Raises:
        RuntimeError: Si falta DATABASE_URL o SUPABASE_DB_PASSWORD.
    """
    load_dotenv(ARCHIVO_ENV)
    url = os.getenv("DATABASE_URL")
    password = os.getenv("SUPABASE_DB_PASSWORD")
    if not url:
        raise RuntimeError(
            "Falta la variable DATABASE_URL en el archivo .env."
        )
    if url.startswith(PREFIJO_URL):
        url = PREFIJO_DRIVER + url[len(PREFIJO_URL):]
    if MARCADOR_PASSWORD not in url:
        return url
    if not password:
        raise RuntimeError(
            "Falta la variable de entorno SUPABASE_DB_PASSWORD."
        )
    # quote_plus evita errores si la contraseña tiene @, #, / u otros
    # caracteres especiales.
    return url.replace(MARCADOR_PASSWORD, quote_plus(password))


class ConexionDB:
    """Administra el engine y las sesiones de SQLAlchemy.

    Por defecto se conecta a la base PostgreSQL de Supabase con la URL del
    archivo .env y la contraseña de la variable SUPABASE_DB_PASSWORD, para
    no dejar contraseñas escritas en el código ni en el repositorio.
    """

    def __init__(
        self, url: Optional[Union[str, URL]] = None, echo: bool = False
    ) -> None:
        """Constructor.

        Args:
            url (Optional[Union[str, URL]]): URL de conexión. Si es None
                se arma con las variables de entorno.
            echo (bool): Si es True, SQLAlchemy muestra las sentencias SQL
                que ejecuta.
        """
        self.__url: URL = make_url(url or url_desde_entorno())
        self.__engine: Engine = create_engine(
            self.__url, echo=echo, pool_pre_ping=True
        )
        self.__fabrica_sesiones: sessionmaker[Session] = sessionmaker(
            bind=self.__engine, expire_on_commit=False
        )

    @property
    def engine(self) -> Engine:
        """Engine de SQLAlchemy asociado a la base de datos."""
        return self.__engine

    @property
    def url(self) -> str:
        """Cadena de conexión con la contraseña oculta."""
        return self.__url.render_as_string(hide_password=True)

    def nueva_sesion(self) -> Session:
        """Crea una sesión nueva para operar con la base de datos.

        Returns:
            Session: Sesión de SQLAlchemy.
        """
        return self.__fabrica_sesiones()

    def probar(self) -> str:
        """Verifica la conexión consultando la versión de PostgreSQL.

        Returns:
            str: Versión informada por la base de datos.
        """
        with self.__engine.connect() as conexion:
            return conexion.execute(text("SELECT version();")).scalar()

    def cerrar(self) -> None:
        """Libera todas las conexiones abiertas del engine."""
        self.__engine.dispose()

    def __repr__(self) -> str:
        """Representación de la conexión (sin la contraseña).

        Returns:
            str: Texto con la cadena de conexión.
        """
        return f"ConexionDB({self.url})"
