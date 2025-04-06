import os
from flask import Flask, render_template, request, flash, url_for, redirect

from .database import connect_db, close_db_connection
from validators import url as validate_url
from urllib.parse import urlparse
from dotenv import load_dotenv
from .logger import logger

import datetime
import psycopg2

load_dotenv()

logger = logger(__name__)

app = Flask(__name__)
app.config['DATABASE_URL'] = os.getenv('DATABASE_URL')
app.secret_key = os.getenv('SECRET_KEY')

@app.errorhandler(404)
def page_not_found(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("errors/500.html"), 500

@app.route('/')
def index():
    """ Отображение главной страницы """
    logger.info("Обработка главной страницы")
    return render_template('index.html')


@app.route('/urls/<int:id>')
def url_detail(id):
    """ Показать детальную информациб по URL """
    logger.info("url_detail")
    try:
        conn = connect_db(app)  # Использование новой функции
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

        # Преобразуем в словарь
        url_data = {'id': url[0], 'name': url[1], 'created_at': url[2]}
        checks_data = [
            {'id': c[0], 'status_code': c[1], 'h1': c[2],
             'title': c[3], 'description': c[4], 'created_at': c[5]}
            for c in checks
        ]

        return render_template('show_one_url.html', url=url_data, checks=checks_data)

    except psycopg2.Error as e:
        flash(f'Ошибка базы данных: {e}', 'danger')
        logger.error(f"DB error: {e}")
        return redirect(url_for('index'))
    finally:
        if 'conn' in locals():
            close_db_connection(conn)  # Закрытие соединения

@app.route('/urls')
def all_urls():
    """ Показать все URLS """
    try:
        conn = connect_db(app)
        with conn.cursor() as cur:
            # Запрос с датой последней проверки
            cur.execute('''
                SELECT 
                    urls.id, 
                    urls.name, 
                    MAX(url_checks.created_at) AS last_check,
                    MAX(url_checks.status_code) AS status_code
                FROM urls
                LEFT JOIN url_checks ON urls.id = url_checks.url_id
                GROUP BY urls.id
                ORDER BY urls.created_at DESC
            ''')
            urls = cur.fetchall()

        urls_data = [
            {'id': u[0], 'name': u[1],
             'last_check': u[2], 'status_code': u[3]}
            for u in urls
        ]

        return render_template('urls.html', urls=urls_data)

    except psycopg2.Error as e:
        flash(f'Ошибка базы данных: {e}', 'danger')
        return redirect(url_for('index'))
    finally:
        if 'conn' in locals():
            close_db_connection(conn)

@app.route('/urls', methods=['POST'])
def add_url():
    """ Проверка и добавление URL """
    input_url = request.form.get('url')
    errors = []

    # Валидация URL
    if not input_url:
        errors.append('URL обязателен для заполнения')
    elif not validate_url(input_url):
        errors.append('Некорректный URL')
    elif len(input_url) > 255:
        errors.append('URL превышает 255 символов')

    if errors:
        flash(errors[0], 'danger')
        return render_template('index.html', errors=errors), 422

    # Нормализация URL
    parsed_url = urlparse(input_url)
    normalized_url = f"{parsed_url.scheme}://{parsed_url.netloc}".lower()

    conn = None
    try:
        conn = connect_db(app)
        with conn.cursor() as cur:
            # Проверка существующего URL
            cur.execute('SELECT id FROM urls WHERE name = %s', (normalized_url,))
            existing_url = cur.fetchone()

            if existing_url:
                flash('Страница уже существует', 'info')
                return redirect(url_for('url_detail', id=existing_url[0]))

            # Вставка нового URL
            created_at = datetime.datetime.now()
            cur.execute(
                "INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id",
                (normalized_url, created_at)
            )
            url_id = cur.fetchone()[0]  # Получаем ID новой записи
            conn.commit()

            flash('Страница успешно добавлена', 'success')
            return redirect(url_for('url_detail', id=url_id))  # Перенаправление

    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        flash(f'Ошибка базы данных: {e}', 'danger')
        return render_template('index.html'), 500

    finally:
        if conn:
            close_db_connection(conn)

@app.route('/urls/<int:id>/checks', methods=['POST'])
def check_url(id):
    """ Проверка URLs """
    try:
        conn = connect_db(app)
        created_at = datetime.datetime.now()
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO url_checks (url_id, created_at) VALUES (%s, %s)",
                (id, created_at)
            )
            conn.commit()
            flash('Страница успешно проверена', 'success')
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        flash(f'Ошибка базы данных: {e}', 'danger')
        logger.error(f"Ошибка проверки: {e}")
    finally:
        if 'conn' in locals():
            close_db_connection(conn)
    return redirect(url_for('url_detail', id=id))