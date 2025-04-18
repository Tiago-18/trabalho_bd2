import os
from flask import Flask, jsonify, request
from datetime import datetime, timedelta
import jwt
from functools import wraps
from funcoes import registar_utilizador, login, get_utilizadores, registar_quarto, verificar_disponibilidade, atualizar_quarto

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

if __name__ == '__main__':
    app.run(debug=True)
