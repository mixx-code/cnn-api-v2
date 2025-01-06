from flask import request, jsonify, g
from config.db_connection import create_db_connection
import jwt
from functools import wraps

SECRET_KEY = 'iki'

def token_required_admin_or_petugas(f):
    """Decorator untuk memverifikasi token di header dan mengizinkan akses admin atau petugas."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'success': False, 'message': 'Token is missing.'}), 403
        
        try:
            # Menghapus "Bearer " di depan token
            token = token.split(" ")[1]
            # Decode token
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            
            # Mendapatkan id pengguna dan jenis akses (admin atau petugas)
            g.user_id = data.get('id')  # Simpan ke global context Flask
            g.is_admin = data.get('is_admin', False)
            g.is_petugas = data.get('id', False)
            
            # Validasi: pengguna harus admin atau petugas
            if not (g.is_admin or g.is_petugas):
                return jsonify({
                    'success': False,
                    'message': 'Your token does not grant access to this API.'
                }), 403

        except Exception as e:
            print(f"Token decoding error: {e}")  # Debugging error
            return jsonify({'success': False, 'message': 'Invalid or expired token.'}), 403
        
        # Lanjutkan ke endpoint
        return f(*args, **kwargs)
    
    return decorated_function

@token_required_admin_or_petugas
def get_total_summary():
    """Retrieve the total count of users, images, and predictions from the database."""
    # Ambil admin_id dari g (global context)
    admin_id = g.user_id
    print(f"Admin ID accessing get_total_summary: {admin_id}")  # Debugging admin ID

    try:
        # Koneksi ke database
        conn = create_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Query untuk menghitung jumlah total petugas
        cursor.execute("SELECT COUNT(*) AS total_petugas FROM petugas")
        total_petugas = cursor.fetchone()['total_petugas']

        # Query untuk menghitung jumlah total admin
        cursor.execute("SELECT COUNT(*) AS total_admin FROM admin")
        total_admin = cursor.fetchone()['total_admin']

        # Query untuk menghitung jumlah total gambar
        cursor.execute("SELECT COUNT(*) AS total_gambar_hama FROM gambar_hama")
        total_gambar_hama = cursor.fetchone()['total_gambar_hama']

        # Query untuk menghitung jumlah total prediksi
        cursor.execute("SELECT COUNT(*) AS total_hasil_prediksi FROM hasil_prediksi")
        total_hasil_prediksi = cursor.fetchone()['total_hasil_prediksi']

        # Query untuk menghitung jumlah total laporan hasil prediksi
        cursor.execute("SELECT COUNT(*) AS total_laporan_hasil_prediksi FROM laporan_hasil_prediksi")
        total_laporan_hasil_prediksi = cursor.fetchone()['total_laporan_hasil_prediksi']

    except Exception as e:
        print(f"Database Error: {e}")  # Debugging error database
        return jsonify({'success': False, 'message': 'Failed to retrieve summary data.'}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

    # Response dengan semua total
    return jsonify({
        'success': True,
        'message': 'Summary data retrieved successfully.',
        'data': {
            'total_petugas': total_petugas,
            'total_admin': total_admin,
            'total_gambar_hama': total_gambar_hama,
            'total_hasil_prediksi': total_hasil_prediksi,
            'total_laporan_hasil_prediksi': total_laporan_hasil_prediksi,
        }
    }), 200
