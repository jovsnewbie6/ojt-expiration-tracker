import os
from app import create_app

app = create_app()

def _is_debug_mode():
    return os.getenv("FLASK_DEBUG", "0") in {"1", "true", "True"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=_is_debug_mode())
