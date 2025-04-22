import psycopg2
import os

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
        cur.execute('CALL realizar_reserva(%s, %s, %s, %s)', (id_quarto, id_utilizador, data_entrada, data_saida))
        conn.commit()
        return 'Reserva efetuada com sucesso!'
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()
