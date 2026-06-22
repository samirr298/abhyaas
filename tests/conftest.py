"""Pytest bootstrap helpers for optional app dependencies.

This test suite imports the Flask application package, which expects
`flask_socketio` to be installed. Some local environments used for testing
do not have that dependency available, so we provide a lightweight stub
before any test modules import the app package.
"""

from __future__ import annotations

import sys
import types


if "flask_socketio" not in sys.modules:
    flask_socketio = types.ModuleType("flask_socketio")

    class SocketIO:  # pragma: no cover - test bootstrap shim
        def __init__(self, *args, **kwargs):
            pass

        def init_app(self, *args, **kwargs):
            return None

    flask_socketio.SocketIO = SocketIO
    sys.modules["flask_socketio"] = flask_socketio


if "pymysql" not in sys.modules:
    pymysql = types.ModuleType("pymysql")

    class _DummyCursor:
        def execute(self, *args, **kwargs):
            return None

        def fetchone(self):
            return None

        def fetchall(self):
            return []

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class _DummyConnection:
        def cursor(self):
            return _DummyCursor()

        def commit(self):
            return None

        def close(self):
            return None

    class _DummyCursors:
        DictCursor = object

    class _DummyErr:
        class DataError(Exception):
            pass

    def connect(*args, **kwargs):
        return _DummyConnection()

    pymysql.connect = connect
    pymysql.cursors = _DummyCursors()
    pymysql.err = _DummyErr()
    sys.modules["pymysql"] = pymysql


if "flask_mail" not in sys.modules:
    flask_mail = types.ModuleType("flask_mail")

    class Mail:  # pragma: no cover - test bootstrap shim
        def __init__(self, *args, **kwargs):
            pass

        def init_app(self, *args, **kwargs):
            return None

        def send(self, *args, **kwargs):
            return None

    class Message:  # pragma: no cover - test bootstrap shim
        def __init__(self, *args, **kwargs):
            self.subject = kwargs.get("subject")
            self.recipients = kwargs.get("recipients", [])
            self.body = kwargs.get("body", "")

    flask_mail.Mail = Mail
    flask_mail.Message = Message
    sys.modules["flask_mail"] = flask_mail


if "dotenv" not in sys.modules:
    dotenv = types.ModuleType("dotenv")

    def load_dotenv(*args, **kwargs):
        return None

    dotenv.load_dotenv = load_dotenv
    sys.modules["dotenv"] = dotenv


if "google.genai" not in sys.modules:
    google_module = sys.modules.get("google")
    if google_module is None:
        google_module = types.ModuleType("google")
        sys.modules["google"] = google_module

    genai_module = types.ModuleType("google.genai")
    types_module = types.ModuleType("google.genai.types")

    class _DummyGenerateContentConfig:  # pragma: no cover - test bootstrap shim
        def __init__(self, *args, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    class _DummyModels:
        def generate_content(self, *args, **kwargs):
            return types.SimpleNamespace(text="")

    class Client:  # pragma: no cover - test bootstrap shim
        def __init__(self, *args, **kwargs):
            self.models = _DummyModels()

    types_module.GenerateContentConfig = _DummyGenerateContentConfig
    genai_module.Client = Client
    genai_module.types = types_module

    google_module.genai = genai_module
    sys.modules["google.genai"] = genai_module
    sys.modules["google.genai.types"] = types_module