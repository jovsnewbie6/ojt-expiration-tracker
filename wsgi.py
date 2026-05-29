import os
from app import create_app

# Create Flask application
app = create_app()

# This file is used by Gunicorn in production: gunicorn wsgi:app
# For local development, use: python -m flask run

if __name__ == "__main__":
    # Local development only
    debug = os.getenv("FLASK_ENV") != "production"
    app.run(host="0.0.0.0", port=5000, debug=debug)
