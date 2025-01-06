from functools import wraps
import time
from flask import jsonify, request
import jwt
from config.db_connection import create_db_connection
import io
from PIL import Image
import base64

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
            is_admin = data.get('is_admin', False)
            is_petugas = data.get('id', False)
            
            # Validasi: pengguna harus admin atau petugas
            if not (is_admin or is_petugas):
                return jsonify({
                    'success': False,
                    'message': 'Your token does not grant access to this API.'
                }), 403
            
            # Simpan informasi ke dalam request context
            request.is_admin = is_admin
            request.is_petugas = is_petugas

        except Exception as e:
            print(f"Token decoding error: {e}")  # Debugging error
            return jsonify({'success': False, 'message': 'Invalid or expired token.'}), 403
        
        # Lanjutkan ke endpoint
        return f(*args, **kwargs)
    
    return decorated_function


@token_required_admin_or_petugas
def get_all_laporan():
    connection = create_db_connection()
    if connection is None:
        return jsonify({'success': False, 'message': 'Gagal menghubungkan ke database!'}), 500

    # Get `cursor` and `limit` from the request arguments
    cursor_id = request.args.get('cursor', None, type=int)
    limit = request.args.get('limit', 10, type=int)

    try:
        cursor = connection.cursor(dictionary=True)
        # cursor.execute("SHOW TABLES;")
        # tables = cursor.fetchall()
        # print("Available tables:", tables)
        print("cursor :", cursor)


        # Build the query with cursor-based pagination
        query = """
            SELECT
                id_laporan,
                prediksi_id,
                petugas_id,
                name,
                gambar_hama,
                prediction_result,
                prediction_percentage,
                tanggal
            FROM
                laporan_hasil_prediksi
        """
        if cursor_id:
            query += " WHERE id_laporan < %s"
        query += " ORDER BY id_laporan DESC LIMIT %s"

        # Execute the query
        if cursor_id:
            cursor.execute(query, (cursor_id, limit))
        else:
            cursor.execute(query, (limit,))
        
        laporan = cursor.fetchall()

        all_laporan = []

        # Parse the laporan
        for laporan in laporan:
            if 'gambar_hama' in laporan:
                image_data = laporan['gambar_hama']
                image = Image.open(io.BytesIO(image_data))
                img_format = image.format.lower()
                buffered = io.BytesIO()
                image.save(buffered, format=image.format)
                img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
                laporan['image_base64'] = f"data:image/{img_format};base64,{img_str}"

            laporan_data = {
                'id_laporan': laporan.get('id_laporan'),
                'prediksi_id': laporan.get('prediksi_id'),
                'petugas_id': laporan.get('petugas_id'),
                'name': laporan.get('name'),
                'prediction_result': laporan.get('prediction_result', 'Unknown'),
                'prediction_percentage': laporan.get('prediction_percentage', '0%'),
                'gambar_hama': laporan['image_base64'],
                'tanggal': laporan.get('tanggal')
            }
            all_laporan.append(laporan_data)

        # Check if there's a next page
        next_cursor = all_laporan[-1]['id_laporan'] if all_laporan else None

        return jsonify({
            'success': True,
            'message': 'laporan retrieved successfully.',
            'data': all_laporan,
            'next_cursor': next_cursor  # Include the next cursor for pagination
        }), 200

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            
@token_required_admin_or_petugas            
def buat_laporan_hasil_prediksi_by_id():
    connection = create_db_connection()
    if connection is None:
        return jsonify({'success': False, 'message': 'Gagal menghubungkan ke database!'}), 500

    # Get `prediksi_id` from the request arguments
    prediksi_id = request.args.get('prediksi_id', None, type=int)
    if not prediksi_id:
        return jsonify({'success': False, 'message': 'Parameter prediksi_id diperlukan!'}), 400

    try:
        cursor = connection.cursor(dictionary=True)

        # Query untuk mengambil data berdasarkan prediksi_id
        query = """
            SELECT
                h.prediksi_id,
                g.petugas_id,
                p.name AS petugas_name,
                g.gambar_hama,
                h.prediction_result,
                h.prediction_percentage,
                h.tanggal
            FROM
                hasil_prediksi h
            JOIN
                gambar_hama g ON h.gambar_id = g.gambar_id
            JOIN
                petugas p ON g.petugas_id = p.petugas_id
            WHERE
                h.prediksi_id = %s
        """

        # Execute query
        cursor.execute(query, (prediksi_id,))
        prediction = cursor.fetchone()

        if not prediction:
            return jsonify({'success': False, 'message': f'Prediksi dengan ID {prediksi_id} tidak ditemukan!'}), 404

        # Konversi gambar menjadi Base64 jika ada
        if 'gambar_hama' in prediction:
            image_data = prediction['gambar_hama']
            img_str = base64.b64encode(image_data).decode('utf-8')  # Konversi bytes ke Base64
            prediction['image_base64'] = f"data:image/jpeg;base64,{img_str}"  # Format Base64 untuk gambar
            del prediction['gambar_hama']  # Hapus data asli untuk menghindari error JSON serialization

        # Buat data hasil prediksi
        prediction_data = {
            'prediksi_id': prediction.get('prediksi_id'),
            'petugas_id': prediction.get('petugas_id'),
            'name': prediction.get('petugas_name'),
            'prediction_result': prediction.get('prediction_result', 'Unknown'),
            'prediction_percentage': prediction.get('prediction_percentage', '0%'),
            'image_base64': prediction.get('image_base64'),
            'tanggal': prediction.get('tanggal')
        }

        # Query untuk memasukkan data ke dalam tabel laporan_hasil_prediksi
        insert_query = """
            INSERT INTO laporan_hasil_prediksi (
                prediksi_id,
                petugas_id,
                name,
                gambar_hama,
                prediction_result,
                prediction_percentage,
                tanggal
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        tanggal = time.strftime('%Y-%m-%d %H:%M:%S')
        # Eksekusi query INSERT
        cursor.execute(insert_query, (
            prediction_data['prediksi_id'],
            prediction_data['petugas_id'],
            prediction_data['name'],
            base64.b64decode(img_str),  # Decode Base64 kembali ke bytes
            prediction_data['prediction_result'],
            prediction_data['prediction_percentage'],
            tanggal
        ))
        connection.commit()

        return jsonify({
            'success': True,
            'message': 'Prediction retrieved and inserted into laporan_hasil_prediksi successfully.',
            'data': prediction_data
        }), 200

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@token_required_admin_or_petugas   
def get_laporan_hasil_prediksi_by_id():
    connection = create_db_connection()
    if connection is None:
        return jsonify({'success': False, 'message': 'Gagal menghubungkan ke database!'}), 500

    # Get `prediksi_id` from the request arguments
    id_laporan = request.args.get('id_laporan', None, type=int)
    if not id_laporan:
        return jsonify({'success': False, 'message': 'Parameter id_laporan diperlukan!'}), 400

    try:
        cursor = connection.cursor(dictionary=True)

        # Query untuk mengambil data berdasarkan prediksi_id
        query = """
            SELECT
                id_laporan ,
                prediksi_id ,
                petugas_id ,
                name,
                gambar_hama,
                prediction_result,
                prediction_percentage,
                tanggal
            FROM
                laporan_hasil_prediksi
            WHERE
                id_laporan = %s
        """

        # Execute query
        cursor.execute(query, (id_laporan,))
        laporan = cursor.fetchone()

        if not laporan:
            return jsonify({'success': False, 'message': f'Prediksi dengan ID {id_laporan} tidak ditemukan!'}), 404

        # Konversi gambar menjadi Base64 jika ada
        if 'gambar_hama' in laporan:
            image_data = laporan['gambar_hama']
            img_str = base64.b64encode(image_data).decode('utf-8')  # Konversi bytes ke Base64
            laporan['image_base64'] = f"data:image/jpeg;base64,{img_str}"  # Format Base64 untuk gambar
            del laporan['gambar_hama']  # Hapus data asli untuk menghindari error JSON serialization

        # Buat data hasil prediksi
        laporan_data = {
            'id_laporan': laporan.get('id_laporan'),
            'prediksi_id': laporan.get('prediksi_id'),
            'petugas_id': laporan.get('petugas_id'),
            'name': laporan.get('name'),
            'image_base64': laporan.get('image_base64'),
            'prediction_result': laporan.get('prediction_result', 'Unknown'),
            'prediction_percentage': laporan.get('prediction_percentage', '0%'),
            'tanggal': laporan.get('tanggal')
        }

        return jsonify({
            'success': True,
            'message': 'Prediction retrieved and inserted into laporan_hasil_prediksi successfully.',
            'data': laporan_data
        }), 200

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# buat dapi delete
@token_required_admin
def delete_laporan_hasil_prediksi(id_laporan):
    """Delete an existing laporan_hasil_prediksi."""
    print(f"ID laporan to delete: {id_laporan}")

    # Delete laporan_hasil_prediksi in database
    try:
        conn = create_db_connection()
        print("Database connected successfully.")  # Debugging message
        cursor = conn.cursor()
        query = """
        DELETE FROM laporan_hasil_prediksi
        WHERE id_laporan = %s
        """

        print(f"Executing query: {query}")  # Debugging query
        cursor.execute(query, (id_laporan,))
        conn.commit()

        # Check if any row was deleted
        if cursor.rowcount == 0:
            return jsonify({'success': False, 'message': 'laporan hasil prediksi not found or unauthorized.'}), 404

    except Exception as e:
        print(f"Error occurred during database operation: {e}")  # Menampilkan detail error
        return jsonify({'success': False, 'message': 'Failed to delete laporan hasil prediksi.'}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

    # Response
    return jsonify({
        'success': True,
        'message': 'laporan hasil prediksi deleted successfully.',
        'data': {
            'id_laporan': id_laporan,
        }
    }), 200
