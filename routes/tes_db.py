from flask import jsonify
from config.db_connection import create_db_connection, close_db_connection

def check_database_connection():
    """
    Check if the application is connected to the database.
    Returns a success message if connected, otherwise an error message.
    """
    connection = create_db_connection()
    
    if connection is None:
        return jsonify({'success': False, 'message': 'Failed to connect to the database.'}), 500

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT 1")  # Execute a simple query
        result = cursor.fetchone()  # Fetch the result
        
        if result:
            return jsonify({'success': True, 'message': 'Database connection is active.'}), 200
        else:
            return jsonify({'success': False, 'message': 'Failed to fetch data from database.'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'Database connection error: {str(e)}'}), 500
    finally:
        close_db_connection(connection)  # Pastikan koneksi ditutup setelah operasi selesai
