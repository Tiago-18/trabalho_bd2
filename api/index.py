from flask import Flask, jsonify
import psycopg2

app = Flask(__name__)

db_config = {
    'dbname': 'db2021153107',
    'user': 'a2021153107',
    'password': 'a2021153107',
    'host': 'aid.estgoh.ipc.pt'
}

@app.route('/')
def home():
    return 'Hello, World! Teste'

@app.route('/about')
def about():
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM utilizadores;')
    emp = cursor.fetchall()

    cursor.close()
    conn.close()
    return jsonify(emp)