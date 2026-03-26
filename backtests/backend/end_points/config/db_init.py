#!/usr/bin/env python
# encoding=utf8

"""
Pure SQLAlchemy Database Initialization for FastAPI.
"""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from db.sqlite.bootstrap import default_seed_dir, default_sqlite_path, ensure_database
from end_points.common.const.consts import DataBase
from end_points.config.global_var import global_var


class DatabaseWrapper:
    """
    Database wrapper that mimics Flask-SQLAlchemy interface
    to maintain compatibility with existing code
    """
    def __init__(self, session, engine=None, engines=None):
        self.session = session
        self.engine = engine
        self.engines = engines or {}

    def get_engine(self, bind_key=None):
        """Get engine for specific bind_key"""
        if bind_key is None:
            return self.engine
        return self.engines.get(bind_key, self.engine)


def _resolve_path(config_dir: Path, raw_path, fallback: Path | None = None) -> Path | None:
    if raw_path:
        path = Path(raw_path)
        if not path.is_absolute():
            path = (config_dir / path).resolve()
        return path
    return fallback


def resolve_database_config(config) -> dict:
    config_dir = Path(config.get("_CONFIG_DIR", Path.cwd()))
    backend = str(config.get("DB_BACKEND", "sqlite")).strip().lower()

    if backend == "sqlite":
        sqlite_path = _resolve_path(
            config_dir,
            config.get("SQLITE_DB_PATH") or config.get("DB_PATH"),
            default_sqlite_path(),
        )
        return {
            "backend": "sqlite",
            "database_path": sqlite_path,
            "main_uri": f"sqlite:///{sqlite_path}",
            "bind_uris": {
                DataBase.stocks: f"sqlite:///{sqlite_path}",
                DataBase.stocks_m: f"sqlite:///{sqlite_path}",
                DataBase.stocks_in_pool: f"sqlite:///{sqlite_path}",
            },
            "engine_kwargs": {
                "connect_args": {"check_same_thread": False},
                "echo": False,
            },
        }

    if backend == "mysql":
        mysql_host = config.get("MYSQL_HOST", config.get("DB_HOST", "localhost"))
        mysql_port = int(config.get("MYSQL_PORT", config.get("DB_PORT", 3306)))
        mysql_user = config.get("MYSQL_USER", config.get("DB_USER", "root"))
        mysql_password = config.get("MYSQL_PASSWORD", config.get("DB_PASSWORD", ""))
        mysql_database = config.get("MYSQL_DATABASE", config.get("DB_NAME", "fintools_backtest"))
        mysql_binds = config.get("MYSQL_BINDS", {}) or {}
        db_base_uri = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/"
        bind_names = {
            DataBase.stocks: mysql_binds.get(DataBase.stocks, DataBase.stocks),
            DataBase.stocks_m: mysql_binds.get(DataBase.stocks_m, DataBase.stocks_m),
            DataBase.stocks_in_pool: mysql_binds.get(DataBase.stocks_in_pool, DataBase.stocks_in_pool),
        }
        return {
            "backend": "mysql",
            "database_path": None,
            "main_uri": db_base_uri + mysql_database,
            "bind_uris": {bind_key: db_base_uri + db_name for bind_key, db_name in bind_names.items()},
            "engine_kwargs": {
                "pool_pre_ping": True,
                "pool_recycle": 3600,
                "pool_size": 5,
                "max_overflow": 15,
                "echo": False,
            },
            "bind_engine_kwargs": {
                "pool_pre_ping": True,
                "pool_recycle": 3600,
                "pool_size": 3,
                "max_overflow": 10,
                "echo": False,
            },
        }

    raise ValueError(f"Unsupported DB_BACKEND: {backend}")


def init_db_for_fastapi(config, global_var):
    """
    Initialize database using pure SQLAlchemy

    Args:
        config: Configuration dictionary
        global_var: Global variables dictionary

    Returns:
        tuple: (success: bool, error_message: str)
    """
    try:
        db_config = resolve_database_config(config)
        database_path = db_config.get("database_path")
        if database_path is not None:
            database_path.parent.mkdir(parents=True, exist_ok=True)

        engine = create_engine(db_config["main_uri"], **db_config["engine_kwargs"])
        seed_dir = _resolve_path(
            Path(config.get("_CONFIG_DIR", Path.cwd())),
            config.get("DB_SEED_DIR"),
            default_seed_dir(),
        )
        ensure_database(
            engine,
            seed_dir=seed_dir,
            bootstrap=bool(config.get("DB_AUTO_BOOTSTRAP", True)),
        )

        if db_config["backend"] == "sqlite":
            bind_engines = {
                DataBase.stocks: engine,
                DataBase.stocks_m: engine,
                DataBase.stocks_in_pool: engine,
            }
        else:
            bind_engines = {
                bind_key: create_engine(bind_uri, **db_config["bind_engine_kwargs"])
                for bind_key, bind_uri in db_config["bind_uris"].items()
            }
        bind_uris = db_config["bind_uris"]

        session_factory = sessionmaker(bind=engine)
        Session = scoped_session(session_factory)

        db_wrapper = DatabaseWrapper(Session, engine=engine, engines=bind_engines)

        global_var['db'] = db_wrapper
        global_var['db_engine'] = engine
        global_var['db_session'] = Session
        global_var['db_engines'] = bind_engines
        global_var['db_binds'] = bind_uris
        global_var['db_backend'] = db_config["backend"]

        print(f"Database initialized successfully: {db_config['main_uri']}")
        return True, ''

    except Exception as e:
        print(f"Failed to initialize database: {e}")
        return False, str(e)


def get_db_session():
    """
    Get database session for dependency injection

    Returns:
        SQLAlchemy session
    """
    # from end_points.config.global_var import global_var
    return global_var.get('db')
