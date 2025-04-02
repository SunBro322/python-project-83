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

@app.route('/urls/<int:id>')
def url_detail(id):
    """Show details of a specific URL"""
    logger.info("url_detail")
    conn = get_db_connection()
    if not conn:
        flash('Ошибка подключения к базе данных', 'danger')
        return redirect(url_for('index'))

    try:
        with conn.cursor() as cur:
            # Получаем данные URL
            cur.execute('SELECT * FROM urls WHERE id = %s', (id,))
            url = cur.fetchone()
            if not url:
                flash('Страница не найдена', 'danger')
                return redirect(url_for('index'))

            # Получаем проверки URL
            cur.execute('''
                SELECT id, status_code, h1, title, description, created_at 
                FROM url_checks 
                WHERE url_id = %s 
                ORDER BY id DESC
            ''', (id,))
            checks = cur.fetchall()

        # Преобразуем в словарь для удобства шаблона
        url_data = {
            'id': url[0],
            'name': url[1],
            'created_at': url[2]
        }
        checks_data = [
            {
                'id': check[0],
                'status_code': check[1],
                'h1': check[2],
                'title': check[3],
                'description': check[4],
                'created_at': check[5]
            } for check in checks
        ]

        return render_template(
            'show_one_url.html',
            url=url_data,
            checks=checks_data
        )

    except psycopg2.Error as e:
        flash(f'Ошибка базы данных: {e}', 'danger')
        logger.info("Ошибка базы данных")
        return redirect(url_for('index'))

    finally:
        close_db_connection(conn)

@app.route('/urls')
def all_urls():
    logger.info("Показать всех пользователей all_urls")
    """Show all URLs"""
    conn = get_db_connection()
    if not conn:
        flash('Ошибка подключения к базе данных', 'danger')
        return redirect(url_for('index'))

    try:
        with conn.cursor() as cur:
            cur.execute('''
                SELECT urls.id, urls.name, 
                    MAX(url_checks.created_at) AS last_check,
                    MAX(url_checks.status_code) AS status_code
                FROM urls
                LEFT JOIN url_checks ON urls.id = url_checks.url_id
                GROUP BY urls.id
                ORDER BY urls.created_at DESC
            ''')
            urls = cur.fetchall()

        urls_data = [
            {
                'id': url[0],
                'name': url[1],
                'last_check': url[2],
                'status_code': url[3]
            } for url in urls
        ]

        return render_template('urls.html', urls=urls_data)

    except psycopg2.Error as e:
        flash(f'Ошибка базы данных: {e}', 'danger')
        return redirect(url_for('index'))

    finally:
        close_db_connection(conn)


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


