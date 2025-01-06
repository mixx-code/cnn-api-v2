from functools import wraps
from flask import jsonify, request
import jwt
from config.db_connection import create_db_connection
import io
from PIL import Image
import base64


SECRET_KEY = 'iki'


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


@token_required_admin
def get_gambar_hama():
    """Endpoint untuk mendapatkan data gambar dari tabel `gambar` dengan cursor-based pagination."""
    connection = create_db_connection()
    if connection is None:
        return jsonify({'success': False, 'message': 'Failed to connect to the database.'}), 500

    try:
        cursor = connection.cursor(dictionary=True)

        # Get query parameters
        cursor_param = request.args.get('cursor', None)  # Cursor untuk pagination (upload_date)
        limit = int(request.args.get('limit', 10))  # Limit jumlah data per halaman (default: 10)

        # Base query
        query = "SELECT gambar_id, petugas_id, gambar_hama, tanggal FROM gambar_hama"

        # Handle cursor (pagination)
        if cursor_param:
            query += " WHERE gambar_id < %s"
            values = (cursor_param,)
        else:
            values = ()

        # Add ordering and limit
        query += " ORDER BY gambar_id DESC LIMIT %s"
        values += (limit,)

        cursor.execute(query, values)
        images = cursor.fetchall()

        # Process image data
        for image in images:
            if 'gambar_hama' in image and isinstance(image['gambar_hama'], bytes):
                image_data = image['gambar_hama']
                pil_image = Image.open(io.BytesIO(image_data))

                # Get image format (e.g., 'JPEG', 'PNG')
                img_format = pil_image.format.lower()

                # Convert PIL image to Base64
                buffered = io.BytesIO()
                pil_image.save(buffered, format=pil_image.format)
                img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')

                # Add Base64 image string to response data with correct prefix
                image['gambar_hama'] = f"data:image/{img_format};base64,{img_str}"

        # Determine next cursor (if more data exists)
        next_cursor = images[-1]['gambar_id'] if len(images) == limit else None

        # Send response with images data
        return jsonify({
            'success': True,
            'message': 'Images retrieved successfully.',
            'data': images,
            'next_cursor': next_cursor  # Cursor untuk halaman berikutnya
        }), 200

    except Exception as e:
        print(f"Database query error: {str(e)}")
        return jsonify({'success': False, 'message': f'Error while fetching data: {str(e)}'}), 500

    finally:
        # Ensure database connection is closed
        if connection.is_connected():
            cursor.close()
            connection.close()

@token_required_admin
def delete_gambar_hama(gambar_id):
    """Delete an existing gambar."""
    print(f"gambar hama ID to delete: {gambar_id}")

    # Delete petugas in database
    try:
        conn = create_db_connection()
        print("Database connected successfully.")  # Debugging message
        cursor = conn.cursor()
        query = """
        DELETE FROM gambar_hama
        WHERE gambar_id = %s
        """

        print(f"Executing query: {query}")  # Debugging query
        cursor.execute(query, (gambar_id,))
        conn.commit()

        # Check if any row was deleted
        if cursor.rowcount == 0:
            return jsonify({'success': False, 'message': 'gambar not found or unauthorized.'}), 404

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
        'message': 'gambar hama deleted successfully.',
        'data': {
            'gambar_id': gambar_id,
        }
    }), 200


# def get_images():
#     """Endpoint untuk mendapatkan data gambar dari tabel `gambar`."""
#     connection = create_db_connection()
#     if connection is None:
#         return jsonify({'success': False, 'message': 'Failed to connect to the database.'}), 500

#     try:
#         cursor = connection.cursor(dictionary=True)

#         # Query to fetch image data
#         cursor.execute("SELECT gambar_id, user_id, gambar_hama, upload_date FROM gambar ORDER BY upload_date DESC;")
#         images = cursor.fetchall()

#         # Process image data
#         for image in images:
#             if 'gambar_hama' in image and isinstance(image['gambar_hama'], bytes):
#                 image_data = image['gambar_hama']
#                 pil_image = Image.open(io.BytesIO(image_data))

#                 # Get image format (e.g., 'JPEG', 'PNG')
#                 img_format = pil_image.format.lower()

#                 # Convert PIL image to Base64
#                 buffered = io.BytesIO()
#                 pil_image.save(buffered, format=pil_image.format)
#                 img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')

#                 # Add Base64 image string to response data with correct prefix
#                 image['gambar_hama'] = f"data:image/{img_format};base64,{img_str}"
                

#         # Send response with images data
#         return jsonify({
#             'success': True,
#             'message': 'Images retrieved successfully.',
#             'data': images
#         }), 200

#     except Exception as e:
#         print(f"Database query error: {str(e)}")
#         return jsonify({'success': False, 'message': f'Error while fetching data: {str(e)}'}), 500

#     finally:
#         # Ensure database connection is closed
#         if connection.is_connected():
#             cursor.close()
#             connection.close()
