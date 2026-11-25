from importlib import import_module

try:
    mysql_connector = import_module("mysql.connector")
except ModuleNotFoundError as exc:
    raise ModuleNotFoundError(
        "Install the MySQL connector with `python -m pip install mysql-connector-python`."
    ) from exc

def get_connection():
    connection = mysql_connector.connect(
        host= "127.0.0.1",
        port = 3306,
        user="root",
        password="root123",
        database="spy_hospital_database"
    )
    return connection
