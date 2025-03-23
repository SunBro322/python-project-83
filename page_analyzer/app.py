import os
from flask import Flask, render_template, request, flash, url_for, redirect
from unicodedata import normalize

from .database import get_db_connection, close_db_connection
from validators import url as validate_url
from urllib.parse import urlparse
from dotenv import load_dotenv
from .logger import logger

import datetime
import psycopg2

load_dotenv()

logger = logger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

@app.errorhandler(404)
def page_not_found(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("errors/500.html"), 500

@app.route('/')
def index():
    """ Show main page """
    logger.info("Обработка главной страницы")
    return render_template('index.html')


@app.route('/urls', methods=['POST'])
def add_url():
    """ Check and add url """
    input_url = request.form.get('url')
    errors = []

    if not input_url:
        errors.append('URL обязателен для заполнения')
    elif not validate_url(input_url):
        errors.append('Некорректный URL')

    if errors:
        flash(errors[0], 'danger')
        return render_template('index.html', errors=errors), 422

    parsed_url = urlparse(input_url)
    normalized_url = f"{parsed_url.scheme}://{parsed_url.netloc}".lower()

    conn = get_db_connection()
    if not conn:
        flash('Ошибка подключения к базе данных', 'danger')
        return render_template('index.html'), 500

    try:
        with (conn.cursor() as cur):
            cur.execute('SELECT id FROM urls WHERE name = %s', (normalized_url,))
            existing_url = cur.fetchone()

            if existing_url:
                flash('Страница уже существует', 'info')
                return redirect(url_for('url_detail', id=existing_url[0]))

            created_at = datetime.datetime.now()
            cur.execute("INSERT INTO urls (name, created_at) "
                        "VALUES (%s, %s) RETURNING id", (normalized_url, created_at))
            url_id = cur.fetchone()[0]
            conn.commit()

            logger.info("Страница успешно добавлена")
            flash('Страница успешно добавлена', 'success')
            return redirect(url_for('url_detail', id=url_id))

    except psycopg2.Error as e:
        conn.rollback()
        flash(f'Ошибка базы данных: {e}', 'danger')
        return render_template('index.html'), 500

    finally:
        close_db_connection(conn)


