from peewee import *

nombre_bd = 'Empresa'
usuario_mysql = 'root' # remplaza por tu usuario de la bd
contraseña = '3124' # remplaza la contraseña por la tuya de la bd
host = 'localhost'
puerto = 3306 # remplaza el puerto si lo has cambiado el por defecto de mysql
db = MySQLDatabase(nombre_bd,user=usuario_mysql,password=contraseña,host=host,port=puerto)

def conectar(): 
    """
    Se conecta a la base de datos MySQL utilizando peewee.
    """
    print(f"Intentando conectar a la siguiente base de datos: '{nombre_bd}'...")
    try:
        db.connect()
        print("Conexión a MySQL establecida exitosamente.")
        return True
    except OperationalError as e:
        print(f"Error al conectar a la base de datos MySQL: {e}")
        return False
    finally:
        if not db.is_closed():
            db.close()
            print("Conexión de prueba cerrada.")

if __name__ == "__main__":
    conectar()