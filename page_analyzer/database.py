import psycopg2


def connect_db(app):
    """Создание подключения к БД через конфиг приложения"""
    try:
        conn = psycopg2.connect(app.config['DATABASE_URL'])
        return conn
    except psycopg2.OperationalError as error:
        app.logger.error(f"Database connection error: {error}")
        raise


def close_db_connection(conn):
    """Закрытие подключения к БД"""
    if conn is not None:
        conn.close()
