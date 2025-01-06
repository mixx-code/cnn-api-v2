from flask import request, jsonify
import jwt
from dotenv import load_dotenv
from config.db_connection import create_db_connection
from functools import wraps
from datetime import datetime, timedelta, timezone
import os

# Memuat variabel dari file .env
load_dotenv()


# Mengambil SECRET_KEY dari variabel lingkungan
SECRET_KEY = 'iki'

# Fungsi untuk membuat token JWT
def generate_token(id, username, is_admin=False):
    # Tentukan apakah id yang diberikan adalah admin_id atau user_id
    payload = {
        'id': id,  # Gunakan 'id' untuk umum, baik admin_id atau user_id
        'username': username,
        'is_admin': is_admin,  # Tambahkan is_admin untuk menandakan apakah itu admin atau user
        'exp': datetime.now(timezone.utc) + timedelta(hours=1)  # Token akan expire dalam 1 jam
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    print(f"Generated token: {token}")  # Debugging token
    return token




# Fungsi untuk memverifikasi token JWT
def verify_token(token):
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return decoded_token
    except jwt.ExpiredSignatureError:
        return None  # Token expired
    except jwt.InvalidTokenError:
        return None  # Invalid token

# Fungsi untuk otentikasi user dan admin
def authenticate_user(username, password):
    conn = create_db_connection()
    cursor = conn.cursor()

    # Cek apakah username dan password cocok di tabel Users
    cursor.execute("SELECT * FROM petugas WHERE username = %s AND password = %s", (username, password))
    petugas = cursor.fetchone()

    if petugas:
        return {'id': petugas[0], 'username': petugas[1], 'is_admin': False}  # user_id, username
    else:
        # Cek apakah username dan password cocok di tabel Admins
        cursor.execute("SELECT * FROM admin WHERE username = %s AND password = %s", (username, password))
        admin = cursor.fetchone()

        if admin:
            return {'id': admin[0], 'username': admin[1], 'is_admin': True}  # admin_id, username


    return None


# API untuk login
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password are required.'}), 400

    # Verifikasi user dan admin
    user_info = authenticate_user(username, password)
    if user_info:
        # Jika berhasil login, generate token
        token = generate_token(user_info['id'], username, user_info['is_admin'])
        return jsonify({
            'success': True,
            'message': 'Login successful.',
            'data': {
                'token': token
            }
        }), 200
    else:
        return jsonify({'success': False, 'message': 'Invalid username or password.'}), 401





# from flask import request, jsonify
# import jwt
# import datetime
# from werkzeug.security import check_password_hash
# from config.db_connection import create_db_connection

# from functools import wraps

# # Secret key untuk menandatangani token JWT
# SECRET_KEY = 'iki'

# # Middleware untuk memverifikasi token
# def token_required(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         token = None

#         if 'Authorization' in request.headers:
#             token = request.headers['Authorization'].split(" ")[1]

#         if not token:
#             return jsonify({'message': 'Token is missing!'}), 403

#         try:
#             data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
#             current_user = data['user_id']
#         except:
#             return jsonify({'message': 'Token is invalid!'}), 403

#         return f(current_user, *args, **kwargs)
#     return decorated_function

# # Route untuk login dan menghasilkan token JWT
# def login():
#     data = request.get_json()
#     email = data.get('email')
#     password = data.get('password')

#     if not email or not password:
#         return jsonify({'message': 'Email dan password diperlukan!'}), 400
#     connection = create_db_connection()
#     cursor = connection.cursor()
#     cursor.execute("SELECT * FROM Users WHERE email = %s", (email,))
#     user = cursor.fetchone()

#     if user:
#         if check_password_hash(user[3], password):  # user[3] adalah password yang di-hash
#             token = jwt.encode({
#                 'user_id': user[0],
#                 'role': user[4],
#                 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
#             }, SECRET_KEY, algorithm='HS256')

#             return jsonify({'token': token}), 200
#         else:
#             return jsonify({'message': 'Login failed! Incorrect email or password.'}), 401
#     else:
#         return jsonify({'message': 'User not found.'}), 404
