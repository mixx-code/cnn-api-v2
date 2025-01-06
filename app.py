from flask import Flask, request
from flask_cors import CORS
from routes import tes_db
from routes.admin import delete_admin, edit_admin, get_all_admin, register_admin
from routes.auth import login
from routes.gambar_hama import delete_gambar_hama, get_gambar_hama
from routes.laporan_hasil_prediksi import buat_laporan_hasil_prediksi_by_id, delete_laporan_hasil_prediksi, get_all_laporan, get_laporan_hasil_prediksi_by_id
from routes.hasil_prediksi import delete_hasil_prediksi, get_all_predictions, get_hasil_prediksi_by_petugas_id
from routes.total_data_tabel import  get_total_summary
from routes.prediksi_hama import prediksi_hama
from routes.petugas import delete_petugas, edit_petugas, get_all_petugas, register_petugas
from dotenv import load_dotenv
import os

# Memuat variabel dari file .env
load_dotenv()

app = Flask(__name__)


# Enable CORS for specified origins
# CORS(app, origins=["http://localhost:3000", "http://your-frontend-url.com"])
CORS(app, resources={r"/*": {
    "origins": "*",  # Mengizinkan semua origin
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"]
}})

# Fungsi untuk logging request sebelum diproses
@app.before_request
def log_request_info():
    print('Headers:', request.headers)
    print('Body:', request.get_data())

# ===================== ini route api Login ==========================================

# Route untuk login 1
app.add_url_rule('/login', 'login', login, methods=['POST'])

# ===================== Penutup route api Login ======================================

# ===================== ini route api ADMIN ======================================

# Route untuk register admin 2
app.add_url_rule('/register-admin', 'register_admin', register_admin, methods=['POST'])

# Route untuk ambil data semua admin 3
app.add_url_rule('/get-all-admin', 'get_all_admin', get_all_admin, methods=['GET'])

# Route untuk edit data admin 4
app.add_url_rule('/edit-admin/<int:admin_id>', 'edit-admin', edit_admin, methods=['PUT'])

# Route untuk edit data admin 5
app.add_url_rule('/delete-admin/<int:admin_id>', 'delete-admin', delete_admin, methods=['DELETE'])

# ===================== Penutup route api ADMIN ======================================

# ===================== ini route api Petugas ======================================

# Route untuk registrasi petugas 6
app.add_url_rule('/register-petugas', 'register_petugas', register_petugas, methods=['POST'])

# Route untuk ambil data semua petugas 7
app.add_url_rule('/get-all-petugas', 'get_all_petugas', get_all_petugas, methods=['GET'])

# Route untuk edit data petugas 8
app.add_url_rule('/edit-petugas/<int:petugas_id>', 'edit-petugas', edit_petugas, methods=['PUT'])

# Route untuk edit data petugas 9
app.add_url_rule('/delete-petugas/<int:petugas_id>', 'delete-petugas', delete_petugas, methods=['DELETE'])

# ===================== Penutup route api Petugas ======================================

# ===================== ini route api melakukan prediksi ======================================

# Route untuk upload image dan prediksi 10
app.add_url_rule('/upload', 'upload_image', prediksi_hama, methods=['POST'])

# ===================== Penutup route api melakukan prediksi ======================================

# ===================== ini route api hasil prediksi ==========================================

# Route untuk ambil data hasil prediksi 11
app.add_url_rule('/list_predictions', 'get_all_predictions', get_all_predictions, methods=['GET'])

# Route untuk delete data hasil prediksi 12
app.add_url_rule('/delete-hasil-prediksi/<int:prediksi_id>', 'delete-hasil-prediksi', delete_hasil_prediksi, methods=['DELETE'])

# Route untuk ambil data hasil prediksi by petugas_id 13
app.add_url_rule('/predictions-by-petugas-id/<int:petugas_id>', 'predictions-by-petugas-id', get_hasil_prediksi_by_petugas_id, methods=['GET'])

# ===================== Penutup route api hasil prediksi ======================================

# ===================== ini route api laporan ==========================================

# Route untuk ambil data laporan 14
app.add_url_rule('/get-all-laporan', 'get-all-laporan', get_all_laporan, methods=['GET'])

# Route untuk buat data laporan by prediksi_id 15
app.add_url_rule('/buat-laporan-hasil-prediksi-by-id', 'buat-laporan-hasil-prediksi-by-id', buat_laporan_hasil_prediksi_by_id, methods=['POST'])

# Route untuk ambil data laporan by id_laporan 16
app.add_url_rule('/get-laporan-hasil-prediksi-by-id', 'get-laporan-hasil-prediksi-by-id', get_laporan_hasil_prediksi_by_id, methods=['GET'])

# Route untuk delete data delete-laporan-hasil-prediksi 17
app.add_url_rule('/delete-laporan-hasil-prediksi/<int:id_laporan>', 'delete-laporan-hasil-prediksi', delete_laporan_hasil_prediksi, methods=['DELETE'])

# ===================== Penutup route api laporan ======================================


# ===================== ini route api gambar hama ==========================================

# Route untuk ambil data gambar hama 18
app.add_url_rule('/get-gambar-hama', 'get_gambar_hama', get_gambar_hama, methods=['GET'])

# Route untuk delete data gambar hama 19
app.add_url_rule('/delete-gambar-hama/<int:gambar_id>', 'delete-gambar-hama', delete_gambar_hama, methods=['DELETE'])

# ===================== Penutup route api gambar hama ======================================

# ===================== ini route api total summary ==========================================

# Route untuk ambil data jumlah data pada setiap tabel 20
app.add_url_rule('/get-total-summary', 'get_total_summary', get_total_summary, methods=['GET'])

# ===================== Penutup route api total summary ======================================


app.add_url_rule('/tes_db', 'check_db', tes_db.check_database_connection, methods=['GET'])

if __name__ == '__main__':
    app.run(debug=True, port=5001)
