import os

config = {
    "DATABASE_URL": os.getenv("TOUDOU_DATABASE_URL", "sqlite:///todos.db"),
    "DEBUG": os.getenv("TOUDOU_DEBUG", "False").lower() == "true",
    "SECRET_KEY": os.getenv("TOUDOU_FLASK_SECRET_KEY", "secret!")
}







