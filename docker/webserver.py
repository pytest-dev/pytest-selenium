from flask import Flask

app = Flask(__name__)


@app.route("/")
def home():
    return """<h1>Success!</h1><a href="#">Link</a><p>Ё</p>"""
