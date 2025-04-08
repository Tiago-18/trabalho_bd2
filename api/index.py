import os
from flask import Flask, jsonify, request
from datetime import datetime, timedelta
import psycopg2
import jwt

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'mysecretkey')

db_config = {
    'dbname': 'db2021153107',
    'user': 'a2021153107',
    'password': 'a2021153107',
    'host': 'aid.estgoh.ipc.pt'
}


def registar_utilizador(nome, email, password, telefone, tipo):
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()

    try:
        cur.callproc('criar_utilizador', (nome, email, password, telefone, tipo))
        result = cur.fetchone()
        conn.commit()

        if result:
            return result[0]
        else:
            raise Exception('Erro ao registrar utilizador.')
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


@app.route('/')
def home():
    return 'Hello, World!'

@app.route('/about')
def about():
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM utilizadores;')
    emp = cursor.fetchall()

    cursor.close()
    conn.close()
    return jsonify(emp)

@app.route('/registar', methods=['POST'])
def registar():
    dados = request.get_json()

    try:
        mensagem = registar_utilizador(
            dados.get('nome'),
            dados.get('email'),
            dados.get('password'),
            dados.get('telefone'),
            dados.get('tipo')
        )
        return jsonify({'Sucesso': mensagem}), 200

    except Exception as e:
        return jsonify({'Erro': str(e)}), 500

@app.route('/login', methods=['POST'])
def login_endpoint():
    data = request.get_json()
    if "email" not in data or "password" not in data:
        return jsonify({"error": "invalid parameters"}), 400

    user = login(data['email'], data['password'])

    if user is None:
        return jsonify({"error": "Credenciais Incorretas!"}), 404

    token = jwt.encode(
        {'id': user['id'], 'exp': datetime.utcnow() + timedelta(minutes=5)},
        app.config['SECRET_KEY'],
        algorithm='HS256'
    )

    user["token"] = token
    return jsonify(user), 200


def login(email, password):
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    try:
        # Usa SELECT na função, passando os parâmetros
        cursor.callproc("autenticacao", (email, password))
        user_dados = cursor.fetchone()

        if user_dados is None:
            return None

        user = {
            "id": user_dados[0],
            "username": user_dados[1],
            "tipo": user_dados[2]
        }

        return user
    except Exception as error:
        print("Erro ao conectar ao PostgreSQL:", error)
        return None
    finally:
        cursor.close()
        conn.close()