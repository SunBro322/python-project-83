from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    ''' Show main page '''
    return render_template('main.html')