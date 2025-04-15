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

def criar_quarto(numero, tipo, capacidade, preco_noite, caracteristicas):
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
