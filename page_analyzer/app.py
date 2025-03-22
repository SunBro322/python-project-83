import os
from flask import Flask, render_template, request, flash, url_for, redirect
from .database import get_db_connection, close_db_connection
from validators import url as validate_url
from urllib.parse import urlparse
from dotenv import load_dotenv
from .logger import logger


load_dotenv()

logger = logger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')


@app.route('/')
def index():
    """ Show main page """
    logger.info("Обработка главной страницы")
    return render_template('main.html')

@app.route('/url/<id>')
def url_show():
    """ Show one url """
    pass

@app.route('/urls', methods=['POST'])
def urls_all():
    logger.info("Показ всех пользователей")
    """ Show all url """

    pass


def add_urls():
    """ Check and add url """
    input_url = request.form.get('url')

    if not validate_url(input_url):
        flash('Некорретный URL', 'danger')
        return render_template('index.html'), 422


@app.errorhandler(404)
def page_not_found(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("errors/500.html"), 500