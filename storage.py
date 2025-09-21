import psycopg2
import uuid
import xui_api
import datetime
from decimal import Decimal
from config import PG_HOST, PG_NAME, PG_PORT, PG_USER, PG_PASSWORD

connection = psycopg2.connect(
    dbname=PG_NAME,
    user=PG_USER,
    password=PG_PASSWORD,
    host=PG_HOST,
    port=PG_PORT
)

cursor = connection.cursor()

class User():
    def __init__(self, chat_id:int, username:str, subID:str, client_id:str, expire:int=None):
        if not expire:
            date = datetime.datetime.now().timestamp() - 86400
            self.expire = int(date)
        else:
            self.expire = expire
        self.chat_id = chat_id
        self.username = username
        self.subID = subID
        self.client_id = client_id
        

cursor.execute("CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, chat_id BIGINT UNIQUE, username VARCHAR(50), subID VARCHAR(50) UNIQUE, client_id VARCHAR(50) UNIQUE, expire BIGINT)")
cursor.execute("CREATE TABLE IF NOT EXISTS payment_history (id SERIAL PRIMARY KEY, operation_id VARCHAR(50), label VARCHAR(65))")
cursor.execute("CREATE TABLE IF NOT EXISTS promocodes (id SERIAL PRIMARY KEY, name VARCHAR(20) UNIQUE, months INT, price INT, usage INT, users INT[])")
connection.commit()


def add_payment(operation_id:int, label:str):
    cursor.execute(f"INSERT INTO payment_history (operation_id, label) VALUES (%s, %s)", (operation_id, label))
    connection.commit()


async def add_user(user:User):
    try:
        cursor.execute("INSERT INTO users (chat_id, username, subID, client_id, expire) VALUES (%s, %s, %s, %s, %s)", (user.chat_id, user.username, user.subID, user.client_id, user.expire))
    except psycopg2.errors.UniqueViolation as ex:
        print(ex)
        connection.commit()
        return False
    if await xui_api.client.add_vless_user(user):
            connection.commit()
            return True 
    connection.rollback()
    return False


def get_user(chatid:int):
    cursor.execute(f"SELECT * FROM users WHERE chat_id={chatid}")
    data = cursor.fetchone()
    if data != None:
        return User(data[1], data[2], data[3], data[4], data[5])
    return None


def get_user_by_username(username:str):
    cursor.execute(f"SELECT * FROM users WHERE username='{username}'")
    data = cursor.fetchone()
    if data != None:
        return User(data[1], data[2], data[3], data[4], data[5])
    return None


def update_user(user:User):
    cursor.execute("UPDATE users SET subID=%s, client_id=%s, expire=%s WHERE chat_id=%s", (user.subID, user.client_id, user.expire, user.chat_id))
    connection.commit()


async def extend_user(chat_id:int, mounths:int):
    user = get_user(chat_id)
    if not user:
        return
    if user.expire < int(datetime.datetime.now().timestamp()):
        #продление на n мясяц с сегодняшнего дня
        user.expire = int(datetime.datetime.now().timestamp()) + (2629743 * mounths)
    else:
        #продление на n мясяц с дня окночания
        user.expire += 2629743 * mounths
    update_user(user)
    await xui_api.client.update_vless_user(user)


def get_operations_history():
    cursor.execute("SELECT operation_id, label FROM payment_history")
    return cursor.fetchall()


def add_operations_history(operation_id:str, label:str):
    cursor.execute("INSERT INTO payment_history (operation_id, label) VALUES (%s, %s)", (operation_id, label))
    connection.commit()


async def reset_user(username:str):
    user = get_user_by_username(username)
    if user:
        user.expire = int(datetime.datetime.now().timestamp() - 86400)
        update_user(user)
        await xui_api.client.update_vless_user(user)
        return True
    return False
    
    
def sql_get(request: str):
    cursor.execute(request)
    return cursor.fetchall()


def create_promo(name:str, months:int, price:int, usage:int):
    try:
        cursor.execute("INSERT INTO promocodes (name, months, price, usage, users) VALUES (%s, %s, %s, %s, {})", (name, months, price, usage))
    except psycopg2.errors.UniqueViolation as ex:
        return False
    connection.commit()
    return True


def use_promo(name:str, chat_id:int):
    cursor.execute(f"SELECT * FROM promocodes WHERE name = '{name}' AND usage != 0 AND NOT {chat_id} = ANY(users)")
    res = cursor.fetchone()
    if res:
        return {
            "months": res[2],
            "price": res[3]
        }
    return res


def remove_promo(name:str, chat_id:int):
    cursor.execute(f"UPDATE promocodes SET usage = GREATEST(usage - 1, 0) users = ARRAY_APPEND(users, {chat_id}) WHERE name='{name}'")
    connection.commit()