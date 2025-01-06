from functools import wraps
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
def get_all_predictions():
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
                h.prediksi_id,
                g.petugas_id,
                g.gambar_hama,
                h.prediction_result,
                h.prediction_percentage,
                h.tanggal
            FROM
                hasil_prediksi h
            JOIN
                gambar_hama g ON h.gambar_id = g.gambar_id
        """
        if cursor_id:
            query += " WHERE h.prediksi_id < %s"
        query += " ORDER BY h.prediksi_id DESC LIMIT %s"

        # Execute the query
        if cursor_id:
            cursor.execute(query, (cursor_id, limit))
        else:
            cursor.execute(query, (limit,))
        
        predictions = cursor.fetchall()

        all_predictions = []

        # Parse the predictions
        for prediction in predictions:
            if 'gambar_hama' in prediction:
                image_data = prediction['gambar_hama']
                image = Image.open(io.BytesIO(image_data))
                img_format = image.format.lower()
                buffered = io.BytesIO()
                image.save(buffered, format=image.format)
                img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
                prediction['image_base64'] = f"data:image/{img_format};base64,{img_str}"

            prediction_data = {
                'prediksi_id': prediction.get('prediksi_id'),
                'petugas_id': prediction.get('petugas_id'),
                'prediction_result': prediction.get('prediction_result', 'Unknown'),
                'prediction_percentage': prediction.get('prediction_percentage', '0%'),
                'image_base64': prediction['image_base64'],
                'tanggal': prediction.get('tanggal')
            }
            all_predictions.append(prediction_data)

        # Check if there's a next page
        next_cursor = all_predictions[-1]['prediksi_id'] if all_predictions else None

        return jsonify({
            'success': True,
            'message': 'Predictions retrieved successfully.',
            'data': all_predictions,
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
def get_hasil_prediksi_by_petugas_id(petugas_id):
    if not petugas_id:
        return jsonify({'success': False, 'message': 'petugas_id is required.'}), 400

    connection = create_db_connection()
    if connection is None:
        return jsonify({'success': False, 'message': 'Failed to connect to the database.'}), 500

    try:
        cursor = connection.cursor(dictionary=True)

        # Get cursor and limit parameters from the request
        cursor_id = request.args.get('cursor', None, type=int)
        limit = request.args.get('limit', 10, type=int)

        # Validate limit parameter
        if limit <= 0 or limit > 100:
            return jsonify({'success': False, 'message': 'Limit must be between 1 and 100.'}), 400

        # Base query
        query = """
            SELECT
                h.prediksi_id,
                g.gambar_hama,
                h.prediction_result,
                h.prediction_percentage,
                h.all_probabilities,
                h.tanggal
            FROM
                hasil_prediksi h
            JOIN
                gambar_hama g ON h.gambar_id = g.gambar_id
            WHERE
                g.petugas_id = %s
        """

        # Add cursor-based pagination logic
        if cursor_id:
            query += " AND h.prediksi_id < %s"

        query += " ORDER BY h.prediksi_id DESC LIMIT %s"

        # Execute the query with appropriate parameters
        params = (petugas_id, cursor_id, limit) if cursor_id else (petugas_id, limit)
        cursor.execute(query, params)

        predictions = cursor.fetchall()

        # If no predictions found, return an empty result
        if not predictions:
            return jsonify({
                'success': True,
                'message': 'No more predictions available.',
                'data': [],
                'next_cursor': None
            }), 200

        all_predictions = []

        # Process each prediction
        for prediction in predictions:
            # Handle the image BLOB (gambar_hama) and return it as an image in Base64
            if 'gambar_hama' in prediction and prediction['gambar_hama']:
                image_data = prediction['gambar_hama']
                try:
                    image = Image.open(io.BytesIO(image_data))
                    buffered = io.BytesIO()
                    image_format = image.format.lower()
                    image.save(buffered, format=image.format)
                    img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                    prediction['image_base64'] = f"data:image/{image_format};base64,{img_base64}"
                except Exception as e:
                    prediction['image_base64'] = None
                    print(f"Image conversion error: {e}")

            # Build the response data for this prediction
            prediction_data = {
                'prediksi_id': prediction.get('prediksi_id'),
                'prediction_result': prediction.get('prediction_result', 'Unknown'),
                'prediction_percentage': prediction.get('prediction_percentage', '0%'),
                'image_base64': prediction.get('image_base64'),
                'tanggal': prediction.get('tanggal')
            }

            # Add the prediction data to the list
            all_predictions.append(prediction_data)

        # Determine the next cursor (if there are more results)
        next_cursor = all_predictions[-1]['prediksi_id'] if len(all_predictions) == limit else None

        # Return paginated predictions for the user as a JSON response
        return jsonify({
            'success': True,
            'message': 'Predictions retrieved successfully.',
            'data': all_predictions,
            'next_cursor': next_cursor
        }), 200

    except Exception as e:
        print(f"Error: {str(e)}")  # Log the error for debugging
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@token_required_admin
def delete_hasil_prediksi(prediksi_id):
    """Delete an existing hasil prediksi."""
    print(f"hasil prediksi ID to delete: {prediksi_id}")

    # Delete petugas in database
    try:
        conn = create_db_connection()
        print("Database connected successfully.")  # Debugging message
        cursor = conn.cursor()
        query = """
        DELETE FROM hasil_prediksi
        WHERE prediksi_id = %s
        """

        print(f"Executing query: {query}")  # Debugging query
        cursor.execute(query, (prediksi_id,))
        conn.commit()

        # Check if any row was deleted
        if cursor.rowcount == 0:
            return jsonify({'success': False, 'message': 'hasil prediksi not found or unauthorized.'}), 404

    except Exception as e:
        print(f"Error occurred during database operation: {e}")  # Menampilkan detail error
        return jsonify({'success': False, 'message': 'Failed to delete gambar.'}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

    # Response
    return jsonify({
        'success': True,
        'message': 'hasil prediksi deleted successfully.',
        'data': {
            'prediksi_id': prediksi_id,
        }
    }), 200


# def get_predictions_by_petugas_id(petugas_id):
#     if not petugas_id:
#         return jsonify({'success': False, 'message': 'petugas_id is required.'}), 400

#     connection = create_db_connection()
#     if connection is None:
#         return jsonify({'success': False, 'message': 'Gagal menghubungkan ke database!'}), 500

#     try:
#         cursor = connection.cursor(dictionary=True)
#         # Modify the query to join `hasil_prediksi` and `gambar` tables based on petugas_id
#         cursor.execute("""
#             SELECT
#                 h.prediksi_id,
#                 g.gambar_hama,
#                 h.prediction_result,
#                 h.prediction_percentage,
#                 h.all_probabilities,
#                 h.tanggal
#             FROM
#                 hasil_prediksi h
#             JOIN
#                 gambar g ON h.gambar_id = g.gambar_id
#             WHERE
#                 g.petugas_id = %s
#             ORDER BY
#                 h.tanggal DESC;

#         """, (petugas_id,))
        
#         predictions = cursor.fetchall()

#         if not predictions:
#             return jsonify({'success': False, 'message': 'No predictions found for this user.'}), 404

#         all_predictions = []  # To store all prediction data

#         # Process each prediction
#         for prediction in predictions:

#             # Handle the image BLOB (gambar_hama) and return it as an image in Base64
#             if 'gambar_hama' in prediction:
#                 # Convert BLOB data to an image
#                 image_data = prediction['gambar_hama']
#                 image = Image.open(io.BytesIO(image_data))

#                 # Get the image format (e.g., 'JPEG', 'PNG')
#                 img_format = image.format.lower()

#                 # Convert image to bytes and then to Base64
#                 buffered = io.BytesIO()
#                 image.save(buffered, format=image.format)
#                 img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')

#                 # Add Base64 image to the prediction data with the correct prefix
#                 prediction['image_base64'] = f"data:image/{img_format};base64,{img_str}"

#                 # Build the response data for this prediction
#                 prediction_data = {
#                     'prediksi_id': prediction.get('prediksi_id'),
#                     'prediction_result': prediction.get('prediction_result', 'Unknown'),
#                     'prediction_percentage': prediction.get('prediction_percentage', '0%'),
#                     'image_base64': prediction['image_base64'],
#                     'tanggal': prediction.get('tanggal')
#                 }

#                 # Add the prediction data to the list
#                 all_predictions.append(prediction_data)

#         # Return all predictions for the user as a JSON response
#         return jsonify({
#             'success': True,
#             'message': 'Predictions retrieved successfully.',
#             'data': all_predictions
#         }), 200

#     except Exception as e:
#         print(f"Error: {str(e)}")  # Log the error for debugging
#         return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

#     finally:
#         if connection.is_connected():
#             cursor.close()
#             connection.close()
