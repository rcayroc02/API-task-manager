from app.config import Settings


def test_plain_postgres_urls_are_normalized_to_psycopg_driver():
    for url in ("postgres://u:p@host:5432/db", "postgresql://u:p@host:5432/db"):
        settings = Settings(DATABASE_URL=url, SECRET_KEY="x")
        assert settings.DATABASE_URL == "postgresql+psycopg://u:p@host:5432/db"


def test_urls_with_explicit_driver_are_left_untouched():
    url = "postgresql+psycopg://u:p@host:5432/db"

    assert Settings(DATABASE_URL=url, SECRET_KEY="x").DATABASE_URL == url
