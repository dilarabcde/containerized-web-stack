from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return {
        "message": "Containerized Web Stack v2",
        "status": "running"
    }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
