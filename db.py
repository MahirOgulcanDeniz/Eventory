import psycopg2

def get_connection():
    return psycopg2.connect(
        dbname="inventory_db",   # senin DB ismin
        user="postgres",        # PostgreSQL kullanıcı adı
        password="123456", # PostgreSQL şifren
        host="localhost",
        port="5432"
    )
