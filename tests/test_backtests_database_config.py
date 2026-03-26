import copy
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock


SKILL_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = SKILL_ROOT / "backtests" / "backend"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from end_points.config.db_init import init_db_for_fastapi, resolve_database_config
from end_points.init_global import load_runtime_config
from end_points.common.const.consts import DataBase


class BacktestsDatabaseConfigTests(unittest.TestCase):
    def test_default_repo_config_loads_sqlite_settings(self):
        runtime_config = load_runtime_config(str(BACKEND_ROOT / "service.conf"))

        self.assertEqual(runtime_config["DB_BACKEND"], "sqlite")
        self.assertEqual(
            Path(runtime_config["_DB_CONFIG_PATH"]).resolve(),
            (SKILL_ROOT / "config.json").resolve(),
        )
        self.assertEqual(runtime_config["SQLITE_DB_PATH"], ".runtime/database/backtests.sqlite3")
        self.assertTrue(runtime_config["DB_AUTO_BOOTSTRAP"])
        self.assertEqual(
            runtime_config["DB_SEED_DIR"],
            "backtests/backend/backups/backup_20260207_201912/json_export",
        )
        self.assertEqual(
            runtime_config["MYSQL_BINDS"],
            {
                "cn_stocks": "cn_stocks",
                "cn_stocks_m": "cn_stocks_m",
                "cn_stocks_in_pool": "cn_stocks_in_pool",
            },
        )

    def test_mysql_config_switch_is_loaded_from_json(self):
        with tempfile.TemporaryDirectory(prefix="backtests-mysql-config-") as tmpdir:
            tmp_path = Path(tmpdir)
            service_path = tmp_path / "service.conf"
            config_path = tmp_path / "config.json"

            service_path.write_text("DATABASE_CONFIG = './config.json'\n", encoding="utf-8")

            config_data = copy.deepcopy(json.loads((SKILL_ROOT / "config.json").read_text(encoding="utf-8")))
            config_data["database"]["backend"] = "mysql"
            config_data["database"]["mysql"] = {
                "host": "mysql.example.internal",
                "port": 3307,
                "user": "backtests",
                "password": "secret",
                "database": "backtests_prod",
                "binds": {
                    "cn_stocks": "stocks_a",
                    "cn_stocks_m": "stocks_m_a",
                    "cn_stocks_in_pool": "stocks_pool_a",
                },
            }
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            runtime_config = load_runtime_config(str(service_path))

        self.assertEqual(runtime_config["DB_BACKEND"], "mysql")
        self.assertEqual(runtime_config["MYSQL_HOST"], "mysql.example.internal")
        self.assertEqual(runtime_config["MYSQL_PORT"], 3307)
        self.assertEqual(runtime_config["MYSQL_USER"], "backtests")
        self.assertEqual(runtime_config["MYSQL_PASSWORD"], "secret")
        self.assertEqual(runtime_config["MYSQL_DATABASE"], "backtests_prod")
        self.assertEqual(
            runtime_config["MYSQL_BINDS"],
            {
                "cn_stocks": "stocks_a",
                "cn_stocks_m": "stocks_m_a",
                "cn_stocks_in_pool": "stocks_pool_a",
            },
        )

    def test_resolve_database_config_for_sqlite_uses_single_runtime_file(self):
        with tempfile.TemporaryDirectory(prefix="backtests-sqlite-config-") as tmpdir:
            config_dir = Path(tmpdir)
            config = {
                "_CONFIG_DIR": str(config_dir),
                "DB_BACKEND": "sqlite",
                "SQLITE_DB_PATH": ".runtime/database/test-backtests.sqlite3",
            }

            db_config = resolve_database_config(config)

        expected_path = (config_dir / ".runtime/database/test-backtests.sqlite3").resolve()
        self.assertEqual(db_config["backend"], "sqlite")
        self.assertEqual(db_config["database_path"], expected_path)
        self.assertEqual(db_config["main_uri"], f"sqlite:///{expected_path}")
        self.assertEqual(db_config["bind_uris"][DataBase.stocks], f"sqlite:///{expected_path}")
        self.assertEqual(db_config["bind_uris"][DataBase.stocks_m], f"sqlite:///{expected_path}")
        self.assertEqual(db_config["bind_uris"][DataBase.stocks_in_pool], f"sqlite:///{expected_path}")

    def test_resolve_database_config_for_mysql_builds_expected_uris(self):
        config = {
            "_CONFIG_DIR": str(SKILL_ROOT),
            "DB_BACKEND": "mysql",
            "MYSQL_HOST": "mysql.example.internal",
            "MYSQL_PORT": 3307,
            "MYSQL_USER": "backtests",
            "MYSQL_PASSWORD": "secret",
            "MYSQL_DATABASE": "backtests_prod",
            "MYSQL_BINDS": {
                "cn_stocks": "stocks_a",
                "cn_stocks_m": "stocks_m_a",
                "cn_stocks_in_pool": "stocks_pool_a",
            },
        }

        db_config = resolve_database_config(config)

        self.assertEqual(db_config["backend"], "mysql")
        self.assertIsNone(db_config["database_path"])
        self.assertEqual(
            db_config["main_uri"],
            "mysql+pymysql://backtests:secret@mysql.example.internal:3307/backtests_prod",
        )
        self.assertEqual(
            db_config["bind_uris"],
            {
                "cn_stocks": "mysql+pymysql://backtests:secret@mysql.example.internal:3307/stocks_a",
                "cn_stocks_m": "mysql+pymysql://backtests:secret@mysql.example.internal:3307/stocks_m_a",
                "cn_stocks_in_pool": "mysql+pymysql://backtests:secret@mysql.example.internal:3307/stocks_pool_a",
            },
        )

    def test_init_db_for_fastapi_initializes_sqlite_backend(self):
        with tempfile.TemporaryDirectory(prefix="backtests-init-sqlite-") as tmpdir:
            config_dir = Path(tmpdir)
            config = {
                "_CONFIG_DIR": str(config_dir),
                "DB_BACKEND": "sqlite",
                "SQLITE_DB_PATH": ".runtime/database/test-backtests.sqlite3",
                "DB_AUTO_BOOTSTRAP": False,
                "DB_SEED_DIR": "seed",
            }
            engine = object()
            global_state = {}

            with mock.patch("end_points.config.db_init.create_engine", return_value=engine) as create_engine_mock, \
                 mock.patch("end_points.config.db_init.ensure_database", return_value=False) as ensure_database_mock:
                ok, err = init_db_for_fastapi(config, global_state)

        self.assertTrue(ok)
        self.assertEqual(err, "")
        self.assertEqual(create_engine_mock.call_count, 1)
        self.assertEqual(global_state["db_backend"], "sqlite")
        self.assertIs(global_state["db_engine"], engine)
        self.assertEqual(global_state["db_engines"][DataBase.stocks], engine)
        ensure_database_mock.assert_called_once()

    def test_init_db_for_fastapi_initializes_mysql_backend_and_binds(self):
        config = {
            "_CONFIG_DIR": str(SKILL_ROOT),
            "DB_BACKEND": "mysql",
            "MYSQL_HOST": "mysql.example.internal",
            "MYSQL_PORT": 3307,
            "MYSQL_USER": "backtests",
            "MYSQL_PASSWORD": "secret",
            "MYSQL_DATABASE": "backtests_prod",
            "MYSQL_BINDS": {
                "cn_stocks": "stocks_a",
                "cn_stocks_m": "stocks_m_a",
                "cn_stocks_in_pool": "stocks_pool_a",
            },
            "DB_AUTO_BOOTSTRAP": True,
            "DB_SEED_DIR": "seed",
        }
        engine_calls = []

        def fake_create_engine(uri, **kwargs):
            engine = types.SimpleNamespace(uri=uri, kwargs=kwargs)
            engine_calls.append(engine)
            return engine

        global_state = {}
        with mock.patch("end_points.config.db_init.create_engine", side_effect=fake_create_engine) as create_engine_mock, \
             mock.patch("end_points.config.db_init.ensure_database", return_value=False) as ensure_database_mock:
            ok, err = init_db_for_fastapi(config, global_state)

        self.assertTrue(ok)
        self.assertEqual(err, "")
        self.assertEqual(create_engine_mock.call_count, 4)
        self.assertEqual(global_state["db_backend"], "mysql")
        self.assertEqual(global_state["db_engine"].uri, engine_calls[0].uri)
        self.assertEqual(
            global_state["db_binds"],
            {
                "cn_stocks": "mysql+pymysql://backtests:secret@mysql.example.internal:3307/stocks_a",
                "cn_stocks_m": "mysql+pymysql://backtests:secret@mysql.example.internal:3307/stocks_m_a",
                "cn_stocks_in_pool": "mysql+pymysql://backtests:secret@mysql.example.internal:3307/stocks_pool_a",
            },
        )
        ensure_database_mock.assert_called_once_with(
            engine_calls[0],
            seed_dir=(SKILL_ROOT / "seed").resolve(),
            bootstrap=True,
        )


if __name__ == "__main__":
    unittest.main()
