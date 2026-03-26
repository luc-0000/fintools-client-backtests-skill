#!/usr/bin/env python
# encoding=utf8

"""
FastAPI Global Initialization Module

This module provides initialization functions for FastAPI that are compatible
with the existing init_global system used in Flask.
"""

import os
import json
from pathlib import Path
import logging

from end_points.config.db_init import init_db_for_fastapi
from end_points.config.global_var import global_var
from end_points.common.utils.trading_agent_sync import sync_trading_agent_into_backtests


def load_config_file(config_path: str) -> dict:
    """
    Load configuration from a file (Flask-style .conf file)

    Args:
        config_path: Path to the configuration file

    Returns:
        Dictionary with configuration values
    """
    config = {}

    if not os.path.exists(config_path):
        print(f"Warning: Config file not found at {config_path}")
        return config

    try:
        suffix = Path(config_path).suffix.lower()
        with open(config_path, 'r', encoding='utf-8') as f:
            if suffix == '.json':
                config = json.load(f)
            else:
                exec(f.read(), config)
                config = {k: v for k, v in config.items() if not k.startswith('__')}
        config['_CONFIG_DIR'] = os.path.dirname(os.path.abspath(config_path))

    except Exception as e:
        print(f"Error loading config file: {e}")

    return config


def merge_configs(*configs: dict) -> dict:
    merged = {}
    for config in configs:
        if config:
            merged.update(config)
    return merged


def normalize_runtime_config(config: dict) -> dict:
    normalized = dict(config)
    database = normalized.get('database')
    if not isinstance(database, dict):
        return normalized

    common = database.get('common') or {}
    sqlite = database.get('sqlite') or {}
    mysql = database.get('mysql') or {}

    normalized.update({
        'DB_BACKEND': database.get('backend', normalized.get('DB_BACKEND', 'sqlite')),
        'DB_AUTO_BOOTSTRAP': common.get('auto_bootstrap', normalized.get('DB_AUTO_BOOTSTRAP', True)),
        'DB_SEED_DIR': common.get('seed_dir', normalized.get('DB_SEED_DIR')),
        'SQLITE_DB_PATH': sqlite.get('path', normalized.get('SQLITE_DB_PATH')),
        'MYSQL_HOST': mysql.get('host', normalized.get('MYSQL_HOST')),
        'MYSQL_PORT': mysql.get('port', normalized.get('MYSQL_PORT')),
        'MYSQL_USER': mysql.get('user', normalized.get('MYSQL_USER')),
        'MYSQL_PASSWORD': mysql.get('password', normalized.get('MYSQL_PASSWORD')),
        'MYSQL_DATABASE': mysql.get('database', normalized.get('MYSQL_DATABASE')),
        'MYSQL_BINDS': mysql.get('binds', normalized.get('MYSQL_BINDS')),
    })
    return normalized


def load_runtime_config(config_path: str | None = None) -> dict:
    if config_path is None:
        config_path = os.environ.get('CFG_PATH', os.path.join(os.path.dirname(__file__), '..', 'service.conf'))

    if not os.path.isabs(config_path) and not os.path.exists(config_path):
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), config_path))
    else:
        config_path = os.path.abspath(config_path)

    service_config = load_config_file(config_path)
    service_dir = Path(service_config.get('_CONFIG_DIR', Path(config_path).resolve().parent))

    db_config_path = (
        os.environ.get('DB_CFG_PATH')
        or service_config.get('DATABASE_CONFIG')
        or '../../config.json'
    )
    db_config_path = Path(db_config_path)
    if not db_config_path.is_absolute():
        db_config_path = (service_dir / db_config_path).resolve()

    db_config = load_config_file(str(db_config_path))
    merged = normalize_runtime_config(merge_configs(service_config, db_config))
    merged['_SERVICE_CONFIG_PATH'] = str(Path(config_path).resolve())
    merged['_SERVICE_CONFIG_DIR'] = str(service_dir)
    merged['_DB_CONFIG_PATH'] = str(db_config_path)
    if '_CONFIG_DIR' not in merged:
        merged['_CONFIG_DIR'] = str(db_config_path.parent)
    return merged


def init_global(config_path: str = None):
    """
    Initialize global variables for FastAPI application

    Args:
        config_path: Path to the configuration file

    Returns:
        bool: True if initialization successful, False otherwise
    """
    config = load_runtime_config(config_path)

    if not config:
        print("Warning: Using default configuration")
        config = {
            'VERSION_FILE': './version',
            'DB_BACKEND': os.environ.get('DB_BACKEND', 'sqlite'),
            'SQLITE_DB_PATH': os.environ.get('SQLITE_DB_PATH', '../../.runtime/database/backtests.sqlite3'),
            'MYSQL_HOST': os.environ.get('MYSQL_HOST', 'localhost'),
            'MYSQL_PORT': int(os.environ.get('MYSQL_PORT', '3306')),
            'MYSQL_USER': os.environ.get('MYSQL_USER', 'root'),
            'MYSQL_PASSWORD': os.environ.get('MYSQL_PASSWORD', ''),
            'MYSQL_DATABASE': os.environ.get('MYSQL_DATABASE', 'fintools_backtest'),
            '_CONFIG_DIR': os.getcwd(),
        }

    # Read version
    try:
        version_file = config.get('VERSION_FILE', './version.txt')
        if not os.path.isabs(version_file):
            version_base_dir = config.get('_SERVICE_CONFIG_DIR', config.get('_CONFIG_DIR', os.getcwd()))
            version_file = os.path.abspath(os.path.join(version_base_dir, version_file))
        if os.path.exists(version_file):
            with open(version_file, 'r', encoding='utf-8') as f:
                version = f.read().strip()
        else:
            version = 'unknown'
    except Exception as e:
        print(f"Warning: Could not read version file: {e}")
        version = 'unknown'

    global_var['version'] = version

    # Initialize database
    ok, err_msg = init_db_for_fastapi(config, global_var)
    if not ok:
        print(f'Failed to init database: {err_msg}')
        return False

    try:
        sync_result = sync_trading_agent_into_backtests(global_var['db'])
        global_var['trading_agent_sync'] = sync_result
    except Exception as exc:
        logging.exception("Trading agent sync failed during init: %s", exc)

    # # Initialize data tool
    # ok, err_msg = init_data_tool_for_fastapi(config, global_var)
    # if not ok:
    #     print(f'Failed to init data tool: {err_msg}')
    #     return False

    print("FastAPI global initialization completed successfully")
    return True
