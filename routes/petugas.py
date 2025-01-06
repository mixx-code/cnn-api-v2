from flask import request, jsonify
from config.db_connection import create_db_connection
import time
from functools import wraps
import os
from functools import wraps
from flask import request, jsonify
import jwt
# Memuat SECRET_KEY dari environment variable
SECRET_KEY ='iki'


def token_required_admin(f):
    """Decorator to verify token in header and check if the user is admin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'success': False, 'message': 'Token is missing.'}), 403
        
        print(f"Received token: {token}")  # Debugging token
        
        try:
            # Menghapus "Bearer " di depan token
            token = token.split(" ")[1]
            # Decode token
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            
            # Print isi token setelah didekode
            print(f"Decoded token data: {data}")  # Menampilkan isi payload dari token
            
            petugas_id = data['id']  # Ambil id (baik petugas_id atau admin_id)
            is_admin = data['is_admin']  # Cek apakah ini admin
            
            # Jika bukan admin, kembalikan respons bahwa tidak diizinkan
            if not is_admin:
                return jsonify({
                    'success': False,
                    'message': 'Your token does not grant access to this API.'
                }), 403
            
            # Simpan admin_id ke dalam request context
            request.admin_id = petugas_id

        except Exception as e:
            print(f"Token decoding error: {e}")  # Debugging error
            return jsonify({'success': False, 'message': 'Invalid or expired token.'}), 403
        
        # Lanjutkan ke endpoint
        return f(*args, **kwargs)
    
    return decorated_function


# Fungsi untuk registrasi user
@token_required_admin  # Menggunakan decorator untuk memvalidasi token admin
def register_petugas():
    """Register a new petugas."""
    # Parse request data
    data = request.json
    username = data.get('username')
    password = data.get('password')
    name = data.get('name')

    # Validasi input
    if not username or not password or not name:
        return jsonify({'success': False, 'message': 'All fields are required.'}), 400

    # Ambil admin_id dari token
    admin_id = request.admin_id  # Dapatkan admin_id yang sudah diset oleh decorator
    print(f"ini admin id yoo: {admin_id}")  # Menampilkan isi payload dari token

    try:
        # Koneksi ke database
        conn = create_db_connection()
        cursor = conn.cursor()

        # Periksa apakah username sudah ada
        check_query = "SELECT COUNT(*) FROM petugas WHERE username = %s"
        cursor.execute(check_query, (username,))
        result = cursor.fetchone()

        if result[0] > 0:  # Jika username sudah ada
            return jsonify({'success': False, 'message': 'Username already exists.'}), 400

        # Jika username unik, lanjutkan dengan INSERT
        query = """
        INSERT INTO petugas (username, password, name, tanggal)
        VALUES (%s, %s, %s, %s)
        """
        tanggal = time.strftime('%Y-%m-%d %H:%M:%S')
        data = (username, password, name, tanggal)
        cursor.execute(query, data)
        conn.commit()
        petugas_id = cursor.lastrowid  # Return the inserted petugas_id

    except Exception as e:
        print(f"Database Error: {e}")
        return jsonify({'success': False, 'message': 'Failed to register user.'}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

    # Response
    return jsonify({
        'success': True,
        'message': 'User registered successfully.',
        'data': {
            'petugas_id': petugas_id,
            'username': username,
            'name': name
        }
    }), 201

    
# Fungsi untuk get all user
@token_required_admin  # Validasi token admin
def get_all_petugas():
    """Retrieve all petugas from the database with cursor-based pagination."""
    # Ambil admin_id dari token
    admin_id = request.admin_id
    print(f"Admin ID accessing get_all_users: {admin_id}")  # Debugging admin ID

    # Parse cursor and limit from query parameters
    cursor_param = request.args.get('cursor', default=None, type=int)  # Default cursor is None
    limit = request.args.get('limit', default=10, type=int)  # Default limit is 10
    print(f"Cursor: {cursor_param}, Limit: {limit}")  # Debugging pagination details

    try:
    # Koneksi ke database
        conn = create_db_connection()
        cursor = conn.cursor(dictionary=True)  # Gunakan dictionary cursor untuk hasil lebih terstruktur

        # Query untuk mendapatkan pengguna berdasarkan cursor
        if cursor_param:  # Jika cursor disediakan
            query = """
            SELECT * FROM petugas
            WHERE petugas_id < %s AND username NOT LIKE %s
            AND username NOT IN (SELECT username FROM admin)
            ORDER BY petugas_id DESC
            LIMIT %s
            """
            cursor.execute(query, (cursor_param, '%admin%', limit))
        else:  # Jika cursor tidak disediakan (mengambil dari awal)
            query = """
            SELECT * FROM petugas
            WHERE username NOT LIKE %s
            AND username NOT IN (SELECT username FROM admin)
            ORDER BY petugas_id DESC
            LIMIT %s
            """
            cursor.execute(query, ('%admin%', limit))

        petugas = cursor.fetchall()

        # Tentukan cursor berikutnya
        next_cursor = petugas[-1]['petugas_id'] if petugas else None

        # Query untuk mendapatkan total jumlah pengguna
        cursor.execute("""
        SELECT COUNT(*) FROM petugas
        WHERE username NOT LIKE %s
        AND username NOT IN (SELECT username FROM admin)
        """, ('%admin%',))
        total_petugas = cursor.fetchone()['COUNT(*)']



    except Exception as e:
        print(f"Database Error: {e}")  # Debugging error database
        return jsonify({'success': False, 'message': 'Failed to retrieve petugas.'}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

    # Response dengan informasi pagination
    return jsonify({
        'success': True,
        'message': 'petugas retrieved successfully.',
        'data': petugas,
        'next_cursor': next_cursor
    }), 200



# Fungsi untuk edit user
@token_required_admin  # Menggunakan decorator untuk memvalidasi token admin
def edit_petugas(petugas_id):
    """Edit an existing user."""
    # Parse request data
    data = request.json
    username = data.get('username')
    password = data.get('password')
    name = data.get('name')
    print(f"petugas ID : {petugas_id}")
    print(f"username : {username}")
    print(f"password : {password}")
    print(f"name : {name}")

    # Validasi input
    if not username or not password or not name:
        return jsonify({'success': False, 'message': 'All fields are required.'}), 400

    # Update petugas in database
    try:
        conn = create_db_connection()
        print("Database connected successfully.")  # Debugging message
        cursor = conn.cursor()
        query = """
        UPDATE petugas
        SET username = %s, password = %s, name = %s, tanggal = %s
        WHERE petugas_id = %s
        """

        print(f"Executing query: {query}")  # Debugging query
        tanggal = time.strftime('%Y-%m-%d %H:%M:%S')
        data = (username, password, name, tanggal, petugas_id)
        cursor.execute(query, data)
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({'success': False, 'message': 'User not found or unauthorized.'}), 404

    except Exception as e:
        print(f"Error occurred during database operation: {e}")  # Menampilkan detail error
        return jsonify({'success': False, 'message': 'Failed to update user.'}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

    # Response
    return jsonify({
        'success': True,
        'message': 'User updated successfully.',
        'data': {
            'petugas_id': petugas_id,
            'username': username,
            'name': name,
            'tanggal' : tanggal
        }
    }), 200

# Fungsi untuk delete petugas
@token_required_admin  # Menggunakan decorator untuk memvalidasi token admin
def delete_petugas(petugas_id):
    """Delete an existing petugas."""
    print(f"petugas ID to delete: {petugas_id}")

    # Delete petugas in database
    try:
        conn = create_db_connection()
        print("Database connected successfully.")  # Debugging message
        cursor = conn.cursor()
        query = """
        DELETE FROM petugas
        WHERE petugas_id = %s
        """

        print(f"Executing query: {query}")  # Debugging query
        cursor.execute(query, (petugas_id,))
        conn.commit()

        # Check if any row was deleted
        if cursor.rowcount == 0:
            return jsonify({'success': False, 'message': 'pertugas not found or unauthorized.'}), 404

    except Exception as e:
        print(f"Error occurred during database operation: {e}")  # Menampilkan detail error
        return jsonify({'success': False, 'message': 'Failed to delete petugas.'}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

    # Response
    return jsonify({
        'success': True,
        'message': 'admin deleted successfully.',
        'data': {
            'petugas_id': petugas_id,
        }
    }), 200
