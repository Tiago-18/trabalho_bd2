from flask import Flask, jsonify, request
import psycopg2

app = Flask(__name__)

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
    return 'Hello, World! Tiago Freitas Apaixonado'

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

