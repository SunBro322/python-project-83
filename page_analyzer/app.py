from flask import (Flask,
                   render_template,
                   request,
                   flash,
                   url_for,
                   redirect)

from validators import url as validate_url
from urllib.parse import urlparse

app = Flask(__name__)


@app.errorhandler(404)
def page_not_found(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("errors/500.html"), 500

@app.route('/')
def home():
    """ Show main page """
    return render_template('main.html')

@app.route('/url/<id>')
def url_show():
    """ Show one url """
    pass

@app.route('/urls')
def urls_all():
    """ Show all url """
    pass


def add_urls():
    """ Check and add url """
    input_url = request.form.get('url')

    if not validate_url(input_url):
        flash('Некорретный URL', 'danger')
        return render_template('index.html'), 422
