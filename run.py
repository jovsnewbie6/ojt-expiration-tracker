from app import create_app

# This creates the actual app instance that Gunicorn is looking for
app = create_app()

if __name__ == "__main__":
    app.run()
