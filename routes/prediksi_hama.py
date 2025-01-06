# from functools import wraps
# from flask import Flask, request, jsonify
# import os
# import time
# import jwt
# import numpy as np
# from tensorflow.keras.models import load_model
# from tensorflow.keras.preprocessing.image import img_to_array
# from PIL import Image
# from io import BytesIO
# from config.db_connection import create_db_connection
# import json

# SECRET_KEY = 'iki'  # Kunci rahasia untuk JWT

# # Load trained model
# # model = load_model(r'C:\Users\iMixx\OneDrive\Desktop\cnn_api\model_alexnet\pest_classification_alexnet.h5')
# model = load_model(r'C:\Users\iMixx\OneDrive\Desktop\cnn_api_v2\model_alexnet\pest_classification_alexnet.h5')

# # Class names
# # class_names = [
# #     "asiatic_rice_borer", "brown_plant_hopper", "paddy_stem_maggot",
# #     "rice_gall_midge", "rice_leaf_caterpillar", "rice_leaf_hopper",
# #     "rice_leaf_roller", "rice_shell_pest", "rice_stem_fly", "rice_water_weevil",
# #     "thrips", "yellow_rice_borer"
# # ]

# class_names = [
#     "penggerek_batang_padi_asia", "wereng_batang_coklat", "belatung_batang_padi",
#     "lalat_pucuk_padi", "ulat_daun_padi", "wereng_daun_padi",
#     "penggulung_daun_padi", "hama_kulit_padi", "lalat_batang_padi",
#     "kumbang_air_padi", "thrips", "penggerek_batang_padi_kuning"
# ]

# # Helper Functions
# def preprocess_image(image_blob):
#     """Preprocess the image for prediction."""
#     img = Image.open(BytesIO(image_blob))
#     img = img.resize((224, 224))
#     img_array = img_to_array(img)
#     img_array = np.expand_dims(img_array, axis=0)
#     img_array /= 255.0
#     return img_array

# def save_to_gambar_table(image_blob, petugas_id):
#     """Insert image into Gambar table and return its ID."""
#     try:
#         conn = create_db_connection()
#         cursor = conn.cursor()
#         query = """
#         INSERT INTO gambar_hama (petugas_id, gambar_hama, tanggal)
#         VALUES (%s, %s, %s)
#         """
#         tanggal = time.strftime('%Y-%m-%d %H:%M:%S')
#         data = (petugas_id, image_blob, tanggal)
#         cursor.execute(query, data)
#         conn.commit()
#         return cursor.lastrowid  # Return the inserted gambar_id
#     except Exception as e:
#         print(f"Database Error: {e}")
#         return None
#     finally:
#         if conn.is_connected():
#             cursor.close()
#             conn.close()

# def save_to_hasil_prediksi_table(gambar_id, prediction_result, prediction_percentage, all_probabilities):
#     """Insert prediction result into hasil_prediksi table."""
#     try:
#         conn = create_db_connection()
#         cursor = conn.cursor()
#         query = """
#         INSERT INTO hasil_prediksi (gambar_id, prediction_result, prediction_percentage, all_probabilities, tanggal)
#         VALUES (%s, %s, %s, %s, %s)
#         """
#         # Convert prediction_percentage to string
#         prediction_percentage_str = f"{prediction_percentage:.2f}%"  # Format as a percentage string
#         tanggal = time.strftime('%Y-%m-%d %H:%M:%S')
#         data = (gambar_id, prediction_result, prediction_percentage_str, json.dumps(all_probabilities), tanggal)
#         cursor.execute(query, data)
#         conn.commit()
#     except Exception as e:
#         print(f"Database Error: {e}")
#     finally:
#         if conn.is_connected():
#             cursor.close()
#             conn.close()


# def verify_token(token):
#     try:
#         decoded_token = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
#         return decoded_token
#     except jwt.ExpiredSignatureError:
#         return None  # Token expired
#     except jwt.InvalidTokenError:
#         return None  # Invalid token


# # Middleware untuk memverifikasi token
# def token_required(f):
#     @wraps(f)
#     def decorated(*args, **kwargs):
#         auth_header = request.headers.get('Authorization')
#         if not auth_header:
#             return jsonify({'success': False, 'message': 'Token is missing.'}), 401

#         try:
#             token = auth_header.split(" ")[1]  # Mengambil token dari "Bearer <token>"
#             decoded_token = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])  # Verifikasi JWT
#         except jwt.ExpiredSignatureError:
#             return jsonify({'success': False, 'message': 'Token has expired.'}), 401
#         except jwt.InvalidTokenError:
#             return jsonify({'success': False, 'message': 'Invalid token.'}), 401

#         return f(decoded_token, *args, **kwargs)  # Token valid, lanjut ke endpoint
#     return decorated

# # Endpoint `upload_image` dengan token
# @token_required
# def prediksi_hama(decoded_token):
#     # Gunakan informasi dari payload token
#     petugas_id = decoded_token['id']  # Ambil ID user dari token
#     is_admin = decoded_token.get('is_admin', False)

#     # Pastikan file ada di request
#     if 'file' not in request.files:
#         return jsonify({'success': False, 'message': 'No file uploaded.'}), 400

#     file = request.files['file']
#     if not file.filename.endswith(('png', 'jpg', 'jpeg')):
#         return jsonify({'success': False, 'message': 'Invalid file type.'}), 400


#     # Read image as binary (for MEDIUMBLOB)
#     image_blob = file.read()

#     # Preprocess image for prediction
#     processed_image = preprocess_image(image_blob)
#     predictions = model.predict(processed_image)[0]
#     predictions_dict = {class_name: round(prob * 100, 2) for class_name, prob in zip(class_names, predictions)}
#     predicted_index = np.argmax(predictions)
#     predicted_label = class_names[predicted_index]
#     predicted_percentage = predictions[predicted_index] * 100

#     # Save image to Gambar table
#     petugas_id = decoded_token['id']  # Gunakan ID user dari token
#     gambar_id = save_to_gambar_table(image_blob, petugas_id)
#     if not gambar_id:
#         return jsonify({'success': False, 'message': 'Failed to save image to database.'}), 500

#     # Save prediction result to Hasil_Prediksi table
#     save_to_hasil_prediksi_table(gambar_id, predicted_label, predicted_percentage, predictions_dict)

#     # Response
#     return jsonify({
#         'success': True,
#         'message': 'Prediction successful.',
#         'data': {
#             'gambar_id': gambar_id,
#             'predicted_class': predicted_label,
#             'prediction_percentage': predicted_percentage,
#             'all_probabilities': predictions_dict
#         }
#     }), 200


from functools import wraps
from flask import Flask, request, jsonify
import os
import time
import jwt
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
from PIL import Image
from io import BytesIO
from config.db_connection import create_db_connection  # Sesuaikan path dengan koneksi DB Anda
import json

# Konfigurasi Flask dan Secret Key
app = Flask(__name__)
SECRET_KEY = 'iki'  # Kunci rahasia untuk JWT

# Load trained model
model = load_model(r'C:\Users\iMixx\OneDrive\Desktop\cnn_api_v2\model_alexnet\pest_classification_alexnet.h5')

# Class names
class_names = [
    "penggerek_batang_padi_asia", "wereng_batang_coklat", "belatung_batang_padi",
    "lalat_pucuk_padi", "ulat_daun_padi", "wereng_daun_padi",
    "penggulung_daun_padi", "hama_kulit_padi", "lalat_batang_padi",
    "kumbang_air_padi", "thrips", "penggerek_batang_padi_kuning"
]

# Helper Functions
def preprocess_image(image_blob):
    """Preprocess the image for prediction."""
    img = Image.open(BytesIO(image_blob))
    img = img.resize((224, 224))
    img_array = img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array /= 255.0
    return img_array

def save_to_gambar_table(image_blob, petugas_id):
    """Insert image into Gambar table and return its ID."""
    try:
        conn = create_db_connection()
        cursor = conn.cursor()
        query = """
        INSERT INTO gambar_hama (petugas_id, gambar_hama, tanggal)
        VALUES (%s, %s, %s)
        """
        tanggal = time.strftime('%Y-%m-%d %H:%M:%S')
        data = (petugas_id, image_blob, tanggal)
        cursor.execute(query, data)
        conn.commit()
        return cursor.lastrowid  # Return the inserted gambar_id
    except Exception as e:
        print(f"Database Error: {e}")
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def save_to_hasil_prediksi_table(gambar_id, prediction_result, prediction_percentage, all_probabilities):
    """Insert prediction result into hasil_prediksi table."""
    try:
        conn = create_db_connection()
        cursor = conn.cursor()
        query = """
        INSERT INTO hasil_prediksi (gambar_id, prediction_result, prediction_percentage, all_probabilities, tanggal)
        VALUES (%s, %s, %s, %s, %s)
        """
        # Convert prediction_percentage to string
        prediction_percentage_str = f"{prediction_percentage:.2f}%"  # Format as a percentage string
        tanggal = time.strftime('%Y-%m-%d %H:%M:%S')
        data = (gambar_id, prediction_result, prediction_percentage_str, json.dumps(all_probabilities), tanggal)
        cursor.execute(query, data)
        conn.commit()
    except Exception as e:
        print(f"Database Error: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def verify_token(token):
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return decoded_token
    except jwt.ExpiredSignatureError:
        return None  # Token expired
    except jwt.InvalidTokenError:
        return None  # Invalid token

# Middleware untuk memverifikasi token
# Middleware untuk memverifikasi token
# def token_required(f):
#     @wraps(f)
#     def decorated(*args, **kwargs):
#         auth_header = request.headers.get('Authorization')
#         if not auth_header:
#             return jsonify({'success': False, 'message': 'Token is missing.'}), 401

#         try:
#             token = auth_header.split(" ")[1]  # Mengambil token dari "Bearer <token>"
#             decoded_token = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])  # Verifikasi JWT
#             # Debug: Cetak isi token
#             print("Decoded Token:", decoded_token)  # Ini untuk melihat apa yang ada dalam token
#         except jwt.ExpiredSignatureError:
#             return jsonify({'success': False, 'message': 'Token has expired.'}), 401
#         except jwt.InvalidTokenError:
#             return jsonify({'success': False, 'message': 'Invalid token.'}), 401

#         return f(decoded_token, *args, **kwargs)  # Token valid, lanjut ke endpoint
#     return decorated
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'success': False, 'message': 'Token is missing.'}), 401

        try:
            token = auth_header.split(" ")[1]  # Mengambil token dari "Bearer <token>"
            decoded_token = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])  # Verifikasi JWT
            # Debug: Cetak isi token
            print("Decoded Token:", decoded_token)  # Ini untuk melihat apa yang ada dalam token
            petugas_id = decoded_token['id']
            username = decoded_token['username']  # Asumsikan username ada di dalam token
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'message': 'Token has expired.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'message': 'Invalid token.'}), 401

        # Cek apakah petugas_id sudah ada di dalam tabel petugas
        conn = create_db_connection()  # Fungsi untuk membuat koneksi ke database
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM petugas WHERE petugas_id = %s", (petugas_id,))
            petugas = cursor.fetchone()

            # Jika petugas tidak ditemukan, buat data petugas baru
            if not petugas:
                tanggal = time.strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute("""
                    INSERT INTO petugas (petugas_id, name, username, password, tanggal)
                    VALUES (%s, %s, %s, %s, %s)
                """, (petugas_id, username, username, username, tanggal))  # Password disamakan dengan username
                conn.commit()
        except Exception as e:
            print(f"Database Error: {e}")
            return jsonify({'success': False, 'message': 'Database error occurred.'}), 500
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

        return f(decoded_token, *args, **kwargs)  # Token valid, lanjut ke endpoint
    return decorated


# Endpoint `upload_image` dengan token
@app.route('/upload', methods=['POST'])
@token_required
def prediksi_hama(decoded_token):
    # Gunakan informasi dari payload token
    petugas_id = decoded_token['id']  # Ambil ID user dari token
    is_admin = decoded_token.get('is_admin', False)

    # Pastikan file ada di request
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded.'}), 400

    file = request.files['file']
    if not file.filename.endswith(('png', 'jpg', 'jpeg')):
        return jsonify({'success': False, 'message': 'Invalid file type.'}), 400

    # Read image as binary (for MEDIUMBLOB)
    image_blob = file.read()

    # Preprocess image for prediction
    processed_image = preprocess_image(image_blob)
    predictions = model.predict(processed_image)[0]
    predictions_dict = {class_name: round(prob * 100, 2) for class_name, prob in zip(class_names, predictions)}
    predicted_index = np.argmax(predictions)
    predicted_label = class_names[predicted_index]
    predicted_percentage = predictions[predicted_index] * 100

    # Save image to Gambar table
    gambar_id = save_to_gambar_table(image_blob, petugas_id)
    if not gambar_id:
        return jsonify({'success': False, 'message': 'Failed to save image to database.'}), 500

    # Save prediction result to Hasil_Prediksi table
    save_to_hasil_prediksi_table(gambar_id, predicted_label, predicted_percentage, predictions_dict)

    # Response
    return jsonify({
        'success': True,
        'message': 'Prediction successful.',
        'data': {
            'gambar_id': gambar_id,
            'predicted_class': predicted_label,
            'prediction_percentage': predicted_percentage,
            'all_probabilities': predictions_dict
        }
    }), 200

if __name__ == '__main__':
    app.run(debug=True)

