from flask import Flask, jsonify
import time

app = Flask(__name__)


def ts():
    return int(time.time())


@app.route("/")
def mini_project():
    appenv = os.getenv('APPENV')
    resp = jsonify({"message": "I looooove to code in " + appenv, "timestamp": ts()})
    resp.headers["X-Frame-Options"] = "SAMEORIGIN"
    resp.headers["X-XSS-Protection"] = "1; mode=block"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    return resp
