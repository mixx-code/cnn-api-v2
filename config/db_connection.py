import mysql.connector
from mysql.connector import Error

def create_db_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",        # Host database
            user="root",             # Username MySQL Anda
            password="",             # Password MySQL Anda
            database="hama_padi_db_v3"  # Nama database yang ingin digunakan
        )
        if connection.is_connected():
            print("Koneksi ke MySQL berhasil!")
        return connection  # Mengembalikan objek koneksi
    except Error as e:
        print("Error saat menghubungkan ke MySQL:", e)
        return None

def close_db_connection(connection):
    """Menutup koneksi database."""
    try:
        if connection and connection.is_connected():
            connection.close()
            print("Koneksi ke MySQL ditutup.")
    except Error as e:
        print("Error saat menutup koneksi:", e)
