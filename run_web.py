#!/usr/bin/env python3
"""
Entry point for the web application.
"""
import os

from raft_toolkit.web.app import run_server

if __name__ == "__main__":
    host = os.getenv("WEB_HOST", "127.0.0.1")
    port = int(os.getenv("WEB_PORT", 8000))
    reload = os.getenv("WEB_RELOAD", "false").lower() in ("true", "1", "yes")

    run_server(host=host, port=port, reload=reload)
