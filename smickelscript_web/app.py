from flask import Flask, request
from flask_cors import CORS
from smickelscript import compiler

app = Flask(__name__)
CORS(app)


@app.route("/")
def index():
    return {"message": "SmickelScript as a Service"}


@app.route("/compile", methods=["POST"])
def compile():
    try:
        asm = compiler.compile_src(request.get_data().decode("utf-8"))
        message = "Ok"
    except Exception as ex:
        asm = ""
        message = str(ex)
    return {"asm": asm, "message": message}
