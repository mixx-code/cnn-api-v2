from flask import request, jsonify
from config.db_connection import create_db_connection, close_db_connection
import time
from functools import wraps
from flask import request, jsonify
import jwt

# Memuat SECRET_KEY dari environment variable
SECRET_KEY ='iki'

def token_required(f):
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

@token_required  # Menggunakan decorator untuk memvalidasi token admin
def register_admin():
    """Register a new admin."""
    # Parse request data
    data = request.json
    username = data.get('username')
    password = data.get('password')
    name = data.get('name')

    # Validate input
    if not username or not password or not name:
        return jsonify({'success': False, 'message': 'All fields are required.'}), 400

    conn = None
    cursor = None

    try:
        # Create database connection
        conn = create_db_connection()
        if conn is None:
            return jsonify({'success': False, 'message': 'Database connection failed.'}), 500
        
        # Create a cursor
        cursor = conn.cursor()

        # Insert admin into database
        query = """
        INSERT INTO admin (username, password, name, tanggal)
        VALUES (%s, %s, %s, %s)
        """
        tanggal = time.strftime('%Y-%m-%d %H:%M:%S')
        data = (username, password, name, tanggal)
        cursor.execute(query, data)
        conn.commit()
        admin_id = cursor.lastrowid  # Return the inserted admin_id

    except Exception as e:
        print(f"Database Error: {e}")
        return jsonify({'success': False, 'message': 'Failed to register admin.'}), 500

    finally:
        # Ensure cursor and connection are closed
        if cursor:
            cursor.close()
        if conn:
            close_db_connection(conn)

    # Response
    return jsonify({
        'success': True,
        'message': 'Admin registered successfully.',
        'data': {
            'admin_id': admin_id,
            'username': username,
            'name': name
        }
    }), 201

@token_required  # Menggunakan decorator untuk memvalidasi token admin
def get_all_admin():
    """Retrieve all petugas from the database with cursor-based pagination."""
    # Ambil admin_id dari token
    # admin_id = request.admin_id
    # print(f"Admin ID accessing get_all_admin: {admin_id}")  # Debugging admin ID

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
            SELECT * FROM admin
            WHERE admin_id < %s
            ORDER BY admin_id DESC
            LIMIT %s
            """
            cursor.execute(query, (cursor_param, limit))
        else:  # Jika cursor tidak disediakan (mengambil dari awal)
            query = """
            SELECT * FROM admin
            ORDER BY admin_id DESC
            LIMIT %s
            """
            cursor.execute(query, (limit,))

        admin = cursor.fetchall()

        # Tentukan cursor berikutnya
        next_cursor = admin[-1]['admin_id'] if admin else None

        # Query untuk mendapatkan total jumlah pengguna
        cursor.execute("SELECT COUNT(*) FROM admin")
        total_admin = cursor.fetchone()['COUNT(*)']

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
        'message': 'admin retrieved successfully.',
        'data': admin,
        'next_cursor': next_cursor
    }), 200
    
@token_required  # Menggunakan decorator untuk memvalidasi token admin
def edit_admin(admin_id):
    """Edit an existing admin."""
    # Parse request data
    data = request.json
    username = data.get('username')
    password = data.get('password')
    name = data.get('name')
    print(f"admin ID : {admin_id}")
    print(f"username : {username}")
    print(f"password : {password}")
    print(f"name : {name}")

    # Validasi input
    if not username or not password or not name:
        return jsonify({'success': False, 'message': 'All fields are required.'}), 400

    # Update admin in database
    try:
        conn = create_db_connection()
        print("Database connected successfully.")  # Debugging message
        cursor = conn.cursor()
        query = """
        UPDATE admin
        SET username = %s, password = %s, name = %s, tanggal = %s
        WHERE admin_id = %s
        """

        print(f"Executing query: {query}")  # Debugging query
        tanggal = time.strftime('%Y-%m-%d %H:%M:%S')
        data = (username, password, name, tanggal, admin_id)
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
        'message': 'admin updated successfully.',
        'data': {
            'admin_id': admin_id,
            'username': username,
            'password': password,
            'name': name,
            'tanggal' : tanggal
        }
    }), 200
    
    # Fungsi untuk delete admin
@token_required  # Menggunakan decorator untuk memvalidasi token admin
def delete_admin(admin_id):
    """Delete an existing admin."""
    print(f"admin ID to delete: {admin_id}")

    # Delete admin in database
    try:
        conn = create_db_connection()
        print("Database connected successfully.")  # Debugging message
        cursor = conn.cursor()
        query = """
        DELETE FROM admin
        WHERE admin_id = %s
        """

        print(f"Executing query: {query}")  # Debugging query
        cursor.execute(query, (admin_id,))
        conn.commit()

        # Check if any row was deleted
        if cursor.rowcount == 0:
            return jsonify({'success': False, 'message': 'pertugas not found or unauthorized.'}), 404

    except Exception as e:
        print(f"Error occurred during database operation: {e}")  # Menampilkan detail error
        return jsonify({'success': False, 'message': 'Failed to delete admin.'}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

    # Response
    return jsonify({
        'success': True,
        'message': 'admin deleted successfully.',
        'data': {
            'admin_id': admin_id,
        }
    }), 200
