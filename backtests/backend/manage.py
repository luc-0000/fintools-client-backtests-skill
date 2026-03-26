#!/usr/bin/env python
# encoding=utf8

"""
FastAPI Server Entry Point

This is the FastAPI version of manage.py
Run this to start the FastAPI server
"""
import os
import uvicorn
from end_points.init_global import load_config_file

def run_manage():
    """Run FastAPI server with configuration"""
    # Load configuration
    env_dist = os.environ
    config_file = env_dist.get('CFG_PATH', './service.conf')
    config = load_config_file(config_file)

    # Get server configuration or use defaults
    host = config.get('LISTEN', '0.0.0.0')
    port = int(config.get('PORT', 8888))
    debug = config.get('DEBUG', False)

    # Run uvicorn server
    uvicorn.run(
        "end_points.main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug"
    )


if __name__ == '__main__':
    run_manage()
