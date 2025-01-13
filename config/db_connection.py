# local

import mysql.connector
from mysql.connector import Error

def create_db_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",        # Host database
            user="rizki",             # Username MySQL Anda
            password="rizki",             # Password MySQL Anda
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

# ngrok
# import mysql.connector
# from mysql.connector import Error

# def create_db_connection():
#     try:
#         # Menggunakan format host yang benar tanpa tcp://
#         connection = mysql.connector.connect(
#             host="0.tcp.ap.ngrok.io",   # Alamat ngrok
#             port=16895,                  # Port yang dipetakan oleh ngrok untuk MySQL
#             user="rizki",                 # Username MySQL Anda
#             password="rizki",                 # Password MySQL Anda
#             database="hama_padi_db_v3"   # Nama database
#         )

#         if connection.is_connected():
#             print("Koneksi ke MySQL berhasil!")
#         return connection  # Mengembalikan objek koneksi
#     except Error as e:
#         print("Error saat menghubungkan ke MySQL:", e)
#         return None

# def close_db_connection(connection):
#     """Menutup koneksi database."""
#     try:
#         if connection and connection.is_connected():
#             connection.close()
#             print("Koneksi ke MySQL ditutup.")
#     except Error as e:
#         print("Error saat menutup koneksi:", e)
