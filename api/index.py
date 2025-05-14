import os, io
from crypt import methods

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

# Função para registar novo utilizador na aplicação
def registar_utilizador(nome, email, password, telefone, tipo):
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()

    try:
        cur.callproc('registar_utilizador', (nome, email, password, telefone, tipo))
        resultado = cur.fetchone()
        conn.commit()

        return resultado[0]
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

# Função para realizar login na aplicação
def login(email, password):
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    try:
        cursor.callproc("login", (email, password))
        dados_utilizador = cursor.fetchone()

        if dados_utilizador is None:
            return None

        utilizador = {
            "id": dados_utilizador[0],
            "email": dados_utilizador[1],
            "tipo": dados_utilizador[2]
        }

        return utilizador
    except Exception as erro:
        print("Erro ao autenticar utilizador:", erro)
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

# Função para registar novo quarto na aplicação
def registar_quarto(numero, tipo, capacidade, preco_noite, caracteristicas):
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()

    try:
        cur.callproc('registar_quarto', (numero, tipo, capacidade, preco_noite, caracteristicas))
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

# Função para verificar disponibilidade dos quartos em um intervalo de datas
def verificar_disponibilidade_quartos(data_entrada, data_saida):
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    try:
        cur.callproc('verificar_disponibilidade_quartos', (data_entrada, data_saida))
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
                "caracteristicas": quarto[5]
            })

        return quartos_disponiveis
    except Exception as e:
        print("Erro:", e)
    finally:
        cur.close()
        conn.close()

# Função para atualizar dados de um quarto
def atualizar_quarto(quarto_id, tipo, capacidade, preco_noite, caracteristicas):
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()

    try:
        cur.callproc('atualizar_quarto',(quarto_id, tipo, capacidade, preco_noite, caracteristicas))
        mensagem = cur.fetchone()[0]
        conn.commit()
        return mensagem
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

# Função para registar nova reserva
def reservas(data_entrada, data_saida, id_quarto, observacoes,id_utilizador):
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()

    try:
        cur.callproc('realizar_reserva',
                    (id_quarto, id_utilizador, data_entrada, data_saida, observacoes))
        mensagem = cur.fetchone()[0]
        conn.commit()
        return mensagem
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

# Função para realizar pagamento de uma reserva
def pagamentos(reserva_id, utilizador_id):
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()

    try:
        cur.callproc('realizar_pagamento_reserva', (reserva_id, utilizador_id))
        resultado = cur.fetchone()[0];
        conn.commit()

        return resultado
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

# Função para eliminar quarto
def eliminar_quarto(quarto_id):
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()

    try:
        cur.callproc('eliminar_quarto', (quarto_id,))
        mensagem = cur.fetchone()[0]
        conn.commit()
        return mensagem
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

# Endpoint para registar novo utilizador na aplicação
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

# Endpoint de login na aplicação
@app.route('/login', methods=['POST'])
def endpoint_login():
    dados = request.get_json()

    if not dados or 'email' not in dados or 'password' not in dados:
        return jsonify({"erro": "Parâmetros inválidos."}), 400

    utilizador = login(dados['email'], dados['password'])

    if utilizador is None:
        return jsonify({"erro": "Credenciais incorretas!"}), 404

    token = jwt.encode(
        {
            'id': utilizador['id'],
            'tipo': utilizador['tipo'],
            'exp': datetime.utcnow() + timedelta(minutes=5)
        },
        app.config['SECRET_KEY'],
        algorithm='HS256'
    )
    # Verificar
    conn = None
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        cur.callproc('atualizar_estado_reservas')
        conn.commit()
        cur.close()
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'erro': f'Erro ao atualizar estado das reservas: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()

    utilizador["token"] = token
    return jsonify(utilizador), 200

# Endpoint de registar quarto
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
        return jsonify({'Sucesso': mensagem}), 200

    except Exception as e:
        return jsonify({'Erro': str(e)}), 500

# Endpoint para verificar disponibilidade de um quarto entre duas datas fornecidas
@app.route('/quarto/disponibilidade', methods=['GET'])
@autorizacao_tipo('Cliente')
def endpoint_verificar_disponibilidade_quartos():
    dados = request.get_json()

    try:
        mensagem = verificar_disponibilidade_quartos(
            dados['data_entrada'],
            dados['data_saida']
        )

        return jsonify({'Sucesso': mensagem}), 200
    except Exception as e:
        return jsonify({'Erro': str(e)}), 500

# Endpoint para atualizar dados de um quarto
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

        return jsonify({'Sucesso': mensagem}), 200
    except Exception as e:
        return jsonify({'Erro': str(e)}), 500

# Endpoint para eliminar quarto
@app.route('/quartos/eliminar/<int:quarto_id>', methods=['DELETE'])
@autorizacao_tipo('Administrador')
def endpoint_eliminar_quarto(quarto_id):
    try:
        mensagem = eliminar_quarto(quarto_id)
        return jsonify({'mensagem': mensagem}), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

# Endpoint para registar nova reserva
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
            dados['observacoes'],
            id_utilizador
        )
        return jsonify({'Sucesso': mensagem}), 200
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

# Endpoint para listar reservas ativas
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
                "data_checkin": reservas[0].isoformat(),
                "data_checkout": reservas[1].isoformat(),
                "valor_total": reservas[2],
                "data_reserva": reservas[3].isoformat(),
                "numero": reservas[4],
                "tipo": reservas[5],
                "capacidade": reservas[6],
                "caracteristicas": reservas[7],
            })
        return jsonify({'reservas_ativas': reservas_ativas}), 200
    except Exception as e:
        return jsonify({'Erro': str(e)}), 500

# Endpoint para listar reservas ao Administrador
@app.route('/reserva', methods=['GET'])
@autorizacao_tipo('Administrador')
def endpoint_reservas_listarReservas():
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()

    try:
        cur.callproc('listar_todas_reservas')
        resultado = cur.fetchall()
        conn.commit()

        if len(resultado) == 0:
            return "Não existem reservas registadas!"

        reservas = []
        for reserva in resultado:
            reservas.append({
                'reserva_id': reserva[0],
                'data_checkin': reserva[1].isoformat(),
                'data_checkout': reserva[2].isoformat(),
                'valor_total': reserva[3],
                'data_reserva': reserva[4].isoformat(),
                'estado': reserva[5],
                'cliente_id': reserva[6],
                'cliente_nome': reserva[7],
                'cliente_email': reserva[8],
                'numero_quarto': reserva[9],
                'tipo_quarto': reserva[10],
                'capacidade': reserva[11],
                'caracteristicas': reserva[12]
            })
        return jsonify({'reservas': reservas}), 200
    except Exception as e:
        return jsonify({'Erro': str(e)}), 500

# Endpoint para registar pagamento de Cliente
@app.route('/pagamentos', methods=['POST'])
@autorizacao_tipo('Cliente')
def endpoint_realizar_pagamento():
    dados = request.get_json()
    id_utilizador = request.user_id

    try:
        mensagem = pagamentos(
            dados['reserva_id'],
            id_utilizador
        )
        return jsonify({'mensagem': mensagem}), 200
    except Exception as e:
        return jsonify({'Erro': str(e)}), 500

# Endpoint para listar pagamentos de um Cliente
@app.route('/pagamentos/listar', methods=['GET'])
@autorizacao_tipo('Cliente')
def endpoint_listar_pagamento():
    id_utilizador = request.user_id
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()

    try:
        cur.callproc('listar_pagamentos_por_id', (id_utilizador,))
        pagamento = cur.fetchall()
        conn.commit()

        if len(pagamento) == 0:
            return "Não existem pagamentos registados!"

        pagamentos_listar = []
        for p in pagamento:
            pagamentos_listar.append({
                "valor": p[0],
                "metodo_pagamento": p[1],
                "estado": p[2],
                "utilizadores_id": p[3],
                "reserva_id": p[4],
                "data_pagamento": p[5].isoformat() if p[5] is not None else "Não Realizado",
            })
        return jsonify({'Listagem de Pagamentos': pagamentos_listar}), 200
    except Exception as e:
        return jsonify({'Erro': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
