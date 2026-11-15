"""Titik masuk aplikasi Somnipathy Lab.

Jalankan dengan:
    py app.py
atau
    py -m flask --app app run --debug
"""

from backend import create_app

app = create_app()


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=app.config.get("DEBUG", True),
    )
