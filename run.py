from app import create_app
from flask_migrate import upgrade

app = create_app()

with app.app_context():
    try:
        upgrade()
    except Exception as e:
        print("Migration error:", e)

if __name__ == "__main__":
    app.run()