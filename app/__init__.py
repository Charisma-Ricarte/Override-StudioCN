# app/__init__.py

# Optional: expose key app modules
from .server import run_server
from .client import run_client
from .rooms import RoomManager

__all__ = ["run_server", "run_client", "RoomManager"]
