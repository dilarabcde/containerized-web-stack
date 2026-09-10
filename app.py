import os
import psycopg2
from flask import Flask

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


@app.route("/")
def home():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()[0]

        cursor.close()
        connection.close()

        return {
            "message": "Containerized Web Stack v3",
            "status": "running",
            "database": "connected",
            "postgres_version": db_version
        }

    except Exception as error:
        return {
            "status": "error",
            "database": "connection failed",
            "error": str(error)
        }, 500


@app.route("/health")
def health():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT 1;")
        cursor.fetchone()

        cursor.close()
        connection.close()

        return {
            "status": "healthy",
            "application": "running",
            "database": "connected"
        }, 200

    except Exception as error:
        return {
            "status": "unhealthy",
            "application": "running",
            "database": "connection failed",
            "error": str(error)
        }, 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
