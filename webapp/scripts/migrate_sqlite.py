"""Run safe SQLite schema fixes for the web application."""

from app import create_app
from app.utils.db_migrations import ensure_user_role_columns


def main() -> None:
    app = create_app()
    with app.app_context():
        ensure_user_role_columns(app.config["SQLALCHEMY_DATABASE_URI"])
        print("SQLite schema migration completed")


if __name__ == "__main__":
    main()
