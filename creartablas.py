from peewee import *
from conectar import db, conectar


class BaseModel(Model):
    class Meta:
        database = db


class Cliente(BaseModel):
    """ Modelo Clientes """
    dni_cif = CharField(max_length=9, primary_key=True, column_name='DNI_CIF')
    nombre_cliente = CharField(max_length=100, null=False)
    tlf = CharField(max_length=15, null=True, column_name='TELEFONO')
    email = CharField(max_length=100, null=True, column_name='EMAIL')

    class Meta:
        table_name = 'CLIENTE'

class Empleado(BaseModel):
    """ Modelo Empleados """
    dni = CharField(max_length=9, primary_key=True, column_name='DNI_CIF')
    nombre = CharField(max_length=100, null=False)
    jefe = BooleanField(default=False, column_name='JEFE')
    email = CharField(max_length=100, null=True, column_name='EMAIL')

    class Meta:
        table_name = 'EMPLEADOS'

class Proyecto(BaseModel):
    """ Modelo Proyectos """
    id_proyecto = AutoField(primary_key=True, column_name='ID')
    titulo_proyecto = CharField(max_length=150, null=False, column_name='TITULO_PROYECTO')
    descripcion = TextField(null=True, column_name='DESCRIPCION')
    fecha_inicio = DateField(column_name='FECHA_INICIO')
    fecha_fin = DateField(column_name='FECHA_FIN')
    presupuesto = FloatField(column_name='PRESUPUESTO')
    id_cliente = ForeignKeyField(Cliente, backref='proyectos', column_name='ID_CLIENTE', on_delete='CASCADE')
    id_jefe_proyecto = ForeignKeyField(Empleado, backref='proyectos_liderados', column_name='ID_JEFE_PROYECTO', on_delete='SET NULL', null=True)

    class Meta:
        table_name = 'PROYECTOS'

class EmpleadoProyecto(BaseModel):
    """ 
    Tabla intermedia M:N (Empleados-Proyectos)
    Define qué empleados (que pueden ser jefes o no) trabajan en qué proyectos.
    """
    empleado = ForeignKeyField(Empleado, backref='proyectos_asignados', column_name='DNI_CIF_EMPLEADO', on_delete='CASCADE')
    proyecto = ForeignKeyField(Proyecto, backref='empleados_asignados', column_name='ID_PROYECTO', on_delete='CASCADE')

    class Meta:
        table_name = 'EMPLEADOS_PROYECTOS'
        primary_key = CompositeKey('empleado', 'proyecto')


def crear_tablas():
    """
    Crea todas las tablas definidas en los modelos.
    Usa try y except para el manejo de errore.
    """
    try:
        db.connect()
        modelos = [Cliente, Empleado, Proyecto, EmpleadoProyecto]
        
        db.create_tables(modelos)
        
        print("Las tablas han sido creadas con exito.")
        
    except OperationalError as e:
        print(f"Error al crear las tablas: {e}")
    except Exception as e:
        print(f"Error durante la creación de tablas: {e}")
    finally:
        if not db.is_closed():
            db.close()

if __name__ == "__main__":
    if conectar():
        crear_tablas()
    else:
        print("\nERROR. No se pudo conectar a la bd.")