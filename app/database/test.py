from db import get_connection

connection = get_connection()

if connection.is_connected():
    print("Database Is Connected Successfully")
else:
    print("Connection Failed") 