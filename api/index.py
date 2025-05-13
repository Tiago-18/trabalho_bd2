import os, io
from flask import Flask, jsonify, request, send_file
from datetime import datetime, timedelta
import jwt
from functools import wraps
import psycopg2

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'mysecretkey')

def autorizacao_tipo(tipo_necessario):
    def decorator_interno(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = None

            if 'Authorization' in request.headers:
                auth_header = request.headers['Authorization']
                if auth_header.startswith("Bearer "):
                    token = auth_header.split(" ")[1]

            if not token:
                return jsonify({'erro': 'Token não fornecido!'}), 401

            try:
                data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
                request.user_id = data['id']
                request.user_tipo = data['tipo']

                if data['tipo'] != tipo_necessario:
                    return jsonify({'erro': 'Permissão negada para este tipo de utilizador!'}), 403

            except jwt.ExpiredSignatureError:
                return jsonify({'erro': 'Token expirado!'}), 401
            except jwt.InvalidTokenError:
                return jsonify({'erro': 'Token inválido!'}), 401

            return f(*args, **kwargs)
        return wrapper
    return decorator_interno

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
def login(email, password):
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    try:
        cursor.callproc("autenticacao", (email, password))
        user_dados = cursor.fetchone()

        if user_dados is None:
            return None

        user = {
            "id": user_dados[0],
            "email": user_dados[1],
            "tipo": user_dados[2]
        }

        return user
    except Exception as error:
        print("Erro ao autenticar utilizador:", error)
        return None
    finally:
        cursor.close()
        conn.close()
def get_utilizadores():
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT * FROM utilizadores;')
        users = cursor.fetchall()
        return users
    finally:
        cursor.close()
        conn.close()
#Funções em relação as funcionalidades da tabela quarto
def registar_quarto(numero, tipo, capacidade, preco_noite, caracteristicas):
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()

    try:
        cur.callproc('criar_quarto', (numero, tipo, capacidade, preco_noite, caracteristicas))
        result = cur.fetchone()
        conn.commit()

        if result:
            return result[0]
        else:
            raise Exception('Erro ao registar novo quarto!')
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def verificar_disponibilidade(data_entrada, data_saida):
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    try:
        cur.callproc('quartos_disponiveis', (data_entrada, data_saida))
        resultado = cur.fetchall()
        conn.commit()

        if len(resultado) == 0:
            return "Não existem quartos disponíveis para as data fornecidas!"

        quartos_disponiveis = []
        for quarto in resultado:
            quartos_disponiveis.append({
                "id": quarto[0],
                "numero": quarto[1],
                "tipo": quarto[2],
                "capacidade": quarto[3],
                "preco_noite": quarto[4],
                "estado": quarto[5],
                "caracteristicas": quarto[6]
            })

        return quartos_disponiveis

    except Exception as e:
        print("Erro:", e)
    finally:
        cur.close()
        conn.close()

def atualizar_quarto(quarto_id, tipo, capacidade, preco_noite, caracteristicas):
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()

    try:
        cur.execute('CALL atualizar_quarto(%s, %s, %s, %s, %s)', (quarto_id, tipo, capacidade,
                    preco_noite, caracteristicas))
        conn.commit()
        return 'Quarto atualizado com sucesso!'

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def reservas(data_entrada, data_saida, id_quarto, id_utilizador):
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()

    try:
        cur.execute('CALL realizar_reserva(%s, %s, %s, %s)',
                    (id_quarto, id_utilizador, data_entrada, data_saida))
        conn.commit()
        return 'Reserva efetuada com sucesso!'
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
    try:
        utilizadores = get_utilizadores()
        return jsonify(utilizadores)
    except Exception as e:
        return jsonify({'Erro': str(e)}), 500

@app.route('/registar', methods=['POST'])
def endpoint_registar():
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
def endpoint_login():
    data = request.get_json()
    if "email" not in data or "password" not in data:
        return jsonify({"error": "invalid parameters"}), 400

    user = login(data['email'], data['password'])

    if user is None:
        return jsonify({"error": "Credenciais Incorretas!"}), 404

    token = jwt.encode(
        {'id': user['id'], 'tipo': user['tipo'], 'exp': datetime.utcnow() + timedelta(minutes=5)},
        app.config['SECRET_KEY'],
        algorithm='HS256'
    )

    user["token"] = token
    return jsonify(user), 200

@app.route('/quarto/registar', methods=['POST'])
@autorizacao_tipo('Administrador')
def endpoint_registar_quarto():
    dados = request.get_json()

    try:
        mensagem = registar_quarto(
            dados['numero'],
            dados['tipo'],
            dados['capacidade'],
            dados['preco_noite'],
            dados['caracteristicas']
        )
        return jsonify({'mensagem': mensagem}), 200

    except Exception as e:
        return jsonify({'Erro': str(e)}), 500

@app.route('/quarto/disponibilidade', methods=['GET'])
@autorizacao_tipo('Cliente')
def endpoint_verificar_disponibilidade():
    dados = request.get_json()

    try:
        mensagem = verificar_disponibilidade(
            dados['data_entrada'],
            dados['data_saida']
        )

        return jsonify({'mensagem': mensagem}), 200
    except Exception as e:
        return jsonify({'Erro': str(e)}), 500

@app.route('/quarto/atualizar/<int:quarto_id>', methods=['PUT'])
@autorizacao_tipo('Administrador')
def endpoint_atualizar_quarto(quarto_id):
    dados = request.get_json()

    try:
        mensagem = atualizar_quarto(
            quarto_id,
            dados['tipo'],
            dados['capacidade'],
            dados['preco_noite'],
            dados['caracteristicas'],
        )

        return jsonify({'mensagem': mensagem}), 200
    except Exception as e:
        return jsonify({'Erro': str(e)}), 500

@app.route('/reservas', methods=['POST'])
@autorizacao_tipo('Cliente')
def endpoint_reservas():
    dados = request.get_json()
    id_utilizador = request.user_id

    try:
        mensagem = reservas(
            dados['data_entrada'],
            dados['data_saida'],
            dados['id_quarto'],
            id_utilizador
        )
        return jsonify({'mensagem': mensagem}), 200
    except Exception as e:
        return jsonify({'Erro': str(e)}), 500

@app.route('/upload-imagem', methods=['POST'])
@autorizacao_tipo('Administrador')
def upload_imagem():
    if 'imagem' not in request.files or 'quarto_id' not in request.form:
        return jsonify({'erro': 'Parâmetros inválidos'}), 400

    imagem = request.files['imagem'].read()
    quarto_id = request.form['quarto_id']

    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        cur.execute("UPDATE quarto SET imagem = %s WHERE id = %s", (psycopg2.Binary(imagem), quarto_id))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'mensagem': f'Imagem atualizada para o quarto {quarto_id}'}), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/quartos/<int:quarto_id>/imagem', methods=['GET'])
@autorizacao_tipo('Administrador')
def obter_imagem(quarto_id):
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        cur.execute("SELECT imagem FROM quarto WHERE id = %s", (quarto_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row and isinstance(row, (list, tuple)) and row[0]:
            return send_file(io.BytesIO(row[0]), mimetype='image/jpeg')
        else:
            return jsonify({'erro': 'Imagem não encontrada'}), 404

    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/reserva/ativas', methods=['GET'])
@autorizacao_tipo('Cliente')
def endpoint_reservas_listarAtivas():
    id_utilizador = request.user_id
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()

    try:
        cur.callproc('listar_reservas_ativas_por_id', (id_utilizador,))
        resultado = cur.fetchall()
        conn.commit()

        if len(resultado) == 0:
            return "Não existem reservas com estado Ativo!"

        reservas_ativas = []
        for reservas in resultado:
            reservas_ativas.append({
                "data_checkin": reservas[0],
                "data_checkout": reservas[1],
                "valor_total": reservas[2],
                "data_reserva": reservas[3],
                "numero": reservas[4],
                "tipo": reservas[5],
                "capacidade": reservas[6],
                "caracteristicas": reservas[7],
            })
        return jsonify({'reservas_ativas': reservas_ativas}), 200
    except Exception as e:
        return jsonify({'Erro': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
