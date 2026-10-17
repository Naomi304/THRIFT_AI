"""Production entry point for THRIFT_AI.

Runs the Flask app under waitress (a production WSGI server that works on
Windows and Linux). Binds to 0.0.0.0 and the platform-provided $PORT so it
works on Railway / Render / Heroku / a VPS without code changes.

Local:       python serve.py
Production:  defined in Procfile as `web: python serve.py`
"""
import os

from waitress import serve

from Main import app

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))
    print(f"Starting THRIFT_AI (waitress) on http://{host}:{port}")
    serve(app, host=host, port=port)
