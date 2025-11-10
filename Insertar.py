from peewee import *
from datetime import date
from conectar import db, conectar
from creartablas import Cliente, Empleado, Proyecto, EmpleadoProyecto

def insertar_clientes_bulk():
    """
    Inserta clientes usando bulk_create() si la tabla está vacía.
    Usa una lista de diccionarios.
    """
    print("\n--- Insertando Clientes (bulk) ---")
    
    clientes_data_dicts = [
        {'dni_cif': 'E19329838', 'nombre_cliente': 'TechNova Servicios S.L.', 'tlf': '912345678', 'email': 'contacto@technova.es'},
        {'dni_cif': 'H65740417', 'nombre_cliente': 'InnovaSoft S.A.', 'tlf': '934567890', 'email': 'info@innovasoft.com'},
        {'dni_cif': 'H10703833', 'nombre_cliente': 'ElectroCanarias S.L.', 'tlf': '928765432', 'email': 'ventas@electrocanarias.es'},
        {'dni_cif': 'E17889122', 'nombre_cliente': 'DataLink Consulting S.L.', 'tlf': '911234567', 'email': 'contacto@datalink.es'},
        {'dni_cif': 'B79670238', 'nombre_cliente': 'Redes Globales S.A.', 'tlf': '932456789', 'email': 'soporte@redesglobales.com'}
    ]
            
    try:
        db.connect(reuse_if_open=True)
        if Cliente.select().count() == 0:
            Cliente.bulk_create(clientes_data_dicts)
            print("Clientes insertados (bulk) correctamente.")
        else:
            print("Datos de Clientes ya existen. No se insertan de nuevo.")
    except IntegrityError as e:
        print(f"Error de integridad al insertar clientes (bulk): {e}")
    except Exception as e:
        print(f"Error inesperado (clientes bulk): {e}")
    finally:
        if not db.is_closed(): 
            db.close()

def insertar_empleados_bulk():
    """
    Inserta empleados usando bulk_create() si la tabla está vacía.
    Usa el campo booleano 'jefe'.
    """
    print("\n--- Insertando Empleados (bulk) ---")
    
    empleados_data_dicts = [
        {'dni': '17520760G', 'nombre': 'Laura Sánchez', 'jefe': True, 'email': 'laura.sanchez@empresa.local'},
        {'dni': '87744401E', 'nombre': 'Carlos Pérez', 'jefe': False, 'email': 'carlos.perez@empresa.local'},
        {'dni': '60657870Q', 'nombre': 'Marta Gómez', 'jefe': False, 'email': 'marta.gomez@empresa.local'},
        {'dni': '35108908Y', 'nombre': 'Jorge Ruiz', 'jefe': False, 'email': 'jorge.ruiz@empresa.local'},
        {'dni': '13769630J', 'nombre': 'Lucía Hernández', 'jefe': True, 'email': 'lucia.hernandez@empresa.local'},
        {'dni': '26477401P', 'nombre': 'Pablo Díaz', 'jefe': False, 'email': 'pablo.diaz@empresa.local'}
    ]
            
    try:
        db.connect(reuse_if_open=True)
        if Empleado.select().count() == 0:
            Empleado.bulk_create(empleados_data_dicts)
            print("Empleados insertados (bulk) correctamente.")
        else:
            print("Datos de Empleados ya existen. No se insertan de nuevo.")
    except IntegrityError as e:
        print(f"Error de integridad al insertar empleados (bulk): {e}")
    except Exception as e:
        print(f"Error inesperado (empleados bulk): {e}")
    finally:
        if not db.is_closed(): 
            db.close()

def insertar_proyecto(titulo, desc, f_inicio, f_fin, presupuesto, cliente_dni, jefe_dni):
    """
    Inserta un único proyecto usando create().
    Aplica las RESTRICCIONES SEMÁNTICAS antes de insertar:
    1. El empleado debe existir y tener el flag 'jefe' a True.
    2. El jefe no puede tener solapamiento de fechas con otros proyectos que lidere.
    """
    print(f"\n--- Intentando crear proyecto: '{titulo}' ---")
    
    try:
        if isinstance(f_inicio, str): f_inicio = date.fromisoformat(f_inicio)
        if isinstance(f_fin, str): f_fin = date.fromisoformat(f_fin)

        db.connect(reuse_if_open=True)
        try:
            cliente_obj = Cliente.get(Cliente.dni_cif == cliente_dni)
        except Cliente.DoesNotExist:
            print(f"Error: Cliente con DNI/CIF {cliente_dni} no existe.")
            return False
        
        try:
            jefe_obj = Empleado.get(Empleado.dni == jefe_dni)
            if not jefe_obj.jefe:
                print(f"Error de restricción: El empleado {jefe_obj.nombre} ({jefe_dni}) NO es jefe y no puede liderar un proyecto.")
                return False
        except Empleado.DoesNotExist:
            print(f"Error: Empleado (jefe) con DNI {jefe_dni} no existe.")
            return False
        
        proyectos_solapados = Proyecto.select().where(
            (Proyecto.id_jefe_proyecto == jefe_obj) &
            (Proyecto.fecha_inicio <= f_fin) &
            (Proyecto.fecha_fin >= f_inicio)
        )
        
        if proyectos_solapados.exists():
            print(f"Error de restricción: El jefe {jefe_obj.nombre} ya lidera un proyecto en esas fechas.")
            for p in proyectos_solapados:
                print(f"  - Conflicto con: {p.titulo_proyecto} (ID: {p.id_proyecto})")
            return False

        with db.atomic():
            nuevo_proyecto = Proyecto.create(
                titulo_proyecto=titulo,
                descripcion=desc,
                fecha_inicio=f_inicio,
                fecha_fin=f_fin,
                presupuesto=presupuesto,
                id_cliente=cliente_obj,
                id_jefe_proyecto=jefe_obj
            )
            print(f"Proyecto '{titulo}' (ID: {nuevo_proyecto.id_proyecto}) creado con éxito.")
            
            EmpleadoProyecto.create(
                empleado=jefe_obj,
                proyecto=nuevo_proyecto
            )
            print(f"Jefe {jefe_obj.nombre} asignado automáticamente a la tabla EmpleadoProyecto.")
            return True

    except Exception as e:
        print(f"Error inesperado (crear proyecto): {e}")
        return False
    finally:
        if not db.is_closed():
            db.close()

def asignar_empleado_a_proyecto(empleado_dni, proyecto_id):
    """
    Asigna un empleado existente a un proyecto existente (tabla M:N).
    Usa create() (o get_or_create) para una relación individual.
    """
    print(f"\n--- Asignando empleado {empleado_dni} a proyecto {proyecto_id} ---")
    
    try:
        db.connect(reuse_if_open=True)
        
        empleado_obj = Empleado.get(Empleado.dni == empleado_dni)
        proyecto_obj = Proyecto.get(Proyecto.id_proyecto == proyecto_id)
        relacion, creada = EmpleadoProyecto.get_or_create(empleado=empleado_obj,proyecto=proyecto_obj)
        
        if creada:
            print(f"Éxito: Empleado '{empleado_obj.nombre}' asignado a '{proyecto_obj.titulo_proyecto}'.")
        else:
            print(f"Aviso: El empleado '{empleado_obj.nombre}' ya estaba asignado a ese proyecto.")
        
        return True

    except Empleado.DoesNotExist:
        print(f"Error: Empleado con DNI {empleado_dni} no existe.")
        return False
    except Proyecto.DoesNotExist:
        print(f"Error: Proyecto con ID {proyecto_id} no existe.")
        return False
    except Exception as e:
        print(f"Error inesperado (asignar empleado): {e}")
        return False
    finally:
        if not db.is_closed():
            db.close()

if __name__ == "__main__":
    
    print("Iniciando script de inserción...")
    insertar_clientes_bulk()
    insertar_empleados_bulk()

    insertar_proyecto(
        titulo="Rediseño Web TechNova",
        desc="Actualización completa del portal corporativo.",
        f_inicio="2024-01-15",
        f_fin="2024-06-30",
        presupuesto=25000.0,
        cliente_dni="E19329838",
        jefe_dni="17520760G"  # Laura (Es jefa)
    )

    insertar_proyecto(
        titulo="Infraestructura Cloud",
        desc="Migración de servidores a la nube.",
        f_inicio="2024-02-10", # Se solapa con el proyecto anterior
        f_fin="2024-08-15",
        presupuesto=45000.0,
        cliente_dni="H10703833",
        jefe_dni="17520760G" # Laura
    )
    
    insertar_proyecto(
        titulo="Proyecto Post-Verano",
        desc="Desarrollo tras vacaciones.",
        f_inicio="2024-09-01", # No se solapa
        f_fin="2024-12-31",
        presupuesto=30000.0,
        cliente_dni="E17889122",
        jefe_dni="17520760G" # Laura
    )
    
    insertar_proyecto(
        titulo="Sistema ERP InnovaSoft",
        desc="Implementación de un ERP personalizado.",
        f_inicio="2024-03-01",
        f_fin="2024-10-01",
        presupuesto=60000.0,
        cliente_dni="H65740417",
        jefe_dni="87744401E"
    )
    

    asignar_empleado_a_proyecto(
        empleado_dni="87744401E",
        proyecto_id=1
    )
    
    asignar_empleado_a_proyecto(
        empleado_dni="60657870Q",
        proyecto_id=1
    )
    

    asignar_empleado_a_proyecto(
        empleado_dni="13769630J",
        proyecto_id=1
    )