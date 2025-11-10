from peewee import *
from datetime import date
from conectar import db
from creartablas import Cliente, Empleado, Proyecto, EmpleadoProyecto, crear_tablas

def insertar_clientes_bulk():
    """Inserta clientes usando bulk_create() si la tabla está vacía."""
    print("\nInsertando clientes (metodo bulk)")
    
    datos_clientes_dicc = [
        {'dni_cif': 'E19329838', 'nombre_cliente': 'TechNova Servicios S.L.', 'tlf': '912345678', 'email': 'contacto@technova.es'},
        {'dni_cif': 'H65740417', 'nombre_cliente': 'InnovaSoft S.A.', 'tlf': '934567890', 'email': 'info@innovasoft.com'},
        {'dni_cif': 'H10703833', 'nombre_cliente': 'ElectroCanarias S.L.', 'tlf': '928765432', 'email': 'ventas@electrocanarias.es'},
        {'dni_cif': 'E17889122', 'nombre_cliente': 'DataLink Consulting S.L.', 'tlf': '911234567', 'email': 'contacto@datalink.es'},
        {'dni_cif': 'B79670238', 'nombre_cliente': 'Redes Globales S.A.', 'tlf': '932456789', 'email': 'soporte@redesglobales.com'}
    ]
            
    try:
        db.connect(reuse_if_open=True)
        if Cliente.select().count() == 0:
            instancias_clientes = []
            for dato in datos_clientes_dicc:
                # El operador ** desempaqueta el diccionario como argumentos clave=valor.
                instancias_clientes.append(Cliente(**dato))
            
            Cliente.bulk_create(instancias_clientes)
            print("Clientes insertados (metodo bulk) correctamente.")
        else:
            print("Datos de 'Clientes' ya existen. No se insertarán de nuevo.")
    except IntegrityError as e:
        print(f"Error de integridad al insertar clientes (metodo bulk): {e}")
    except Exception as e:
        print(f"Error inesperado al insertar clientes: {e}")
    finally:
        if not db.is_closed():
            db.close()

def insertar_empleados_bulk():
    """Inserta empleados usando bulk_create() si la tabla está vacía."""
    print("\nInsertando Empleados (metodo bulk)")
    
    datos_empleados_dicc = [
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
            instancias_empleados = []
            for dato in datos_empleados_dicc:
                instancias_empleados.append(Empleado(**dato))
            
            Empleado.bulk_create(instancias_empleados)
            print("Empleados insertados (metodo bulk) correctamente.")
        else:
            print("Datos de Empleados ya existen. No se insertan de nuevo.")
    except IntegrityError as e:
        print(f"Error de integridad al insertar empleados (metodo bulk): {e}")
    except Exception as e:
        print(f"Error inesperado al insertar empleados: {e}")
    finally:
        if not db.is_closed():
            db.close()

def insertar_proyecto(titulo, desc, f_inicio, f_fin, presupuesto, dni_cliente, dni_jefe):
    """
    Inserta un único proyecto, aplicando validaciones de jefe y solapamiento de fechas.
    Nota: Se realiza sin bloques de transacción (db.atomic()).
    """
    print(f"\nIntentando crear proyecto: '{titulo}'")
    
    try:
        # Conversión de fechas
        if isinstance(f_inicio, str): f_inicio = date.fromisoformat(f_inicio)
        if isinstance(f_fin, str): f_fin = date.fromisoformat(f_fin)

        db.connect(reuse_if_open=True)
        try:
            obj_cliente = Cliente.get(Cliente.dni_cif == dni_cliente)
        except Cliente.DoesNotExist:
            print(f"Error: Cliente con DNI/CIF {dni_cliente} no existe.")
            return False
        
        try:
            obj_jefe = Empleado.get(Empleado.dni == dni_jefe)
            if not obj_jefe.jefe:
                print(f"Error de restricción: El empleado {obj_jefe.nombre} ({dni_jefe}) NO es jefe y no puede liderar un proyecto.")
                return False
        except Empleado.DoesNotExist:
            print(f"Error: Empleado (jefe) con DNI {dni_jefe} no existe.")
            return False

        proyectos_solapados = Proyecto.select().where(
            (Proyecto.id_jefe_proyecto == obj_jefe) &
            (Proyecto.fecha_inicio <= f_fin) &
            (Proyecto.fecha_fin >= f_inicio)
        )
        
        if proyectos_solapados.exists():
            print(f"Error de restricción: El jefe {obj_jefe.nombre} ya lidera un proyecto en esas fechas.")
            for p in proyectos_solapados:
                print(f"  - Conflicto con: {p.titulo_proyecto} (ID: {p.id_proyecto})")
            return False
        
        nuevo_proyecto = Proyecto.create(
            titulo_proyecto=titulo,
            descripcion=desc,
            fecha_inicio=f_inicio,
            fecha_fin=f_fin,
            presupuesto=presupuesto,
            id_cliente=obj_cliente,
            id_jefe_proyecto=obj_jefe
        )
        print(f"Proyecto '{titulo}' (ID: {nuevo_proyecto.id_proyecto}) creado con éxito.")

        EmpleadoProyecto.create(
            empleado=obj_jefe,
            proyecto=nuevo_proyecto
        )
        print(f"Jefe {obj_jefe.nombre} asignado automáticamente a la tabla EmpleadoProyecto.")
        return True

    except Exception as e:
        print(f"Error inesperado al crear el proyecto: {e}")
        return False
    finally:
        if not db.is_closed():
            db.close()

def asignar_empleado_a_proyecto(dni_empleado, id_proyecto):
    """
    Asigna un empleado existente a un proyecto existente.
    Usa get_or_create para evitar datos duplicados.
    """
    print(f"\n Asignando empleado {dni_empleado} a proyecto {id_proyecto}")
    
    try:
        db.connect(reuse_if_open=True)
        
        obj_empleado = Empleado.get(Empleado.dni == dni_empleado)
        obj_proyecto = Proyecto.get(Proyecto.id_proyecto == id_proyecto)

        relacion, creada = EmpleadoProyecto.get_or_create(
            empleado=obj_empleado,
            proyecto=obj_proyecto
        )
        
        if creada:
            print(f"Éxito: Empleado '{obj_empleado.nombre}' asignado a '{obj_proyecto.titulo_proyecto}'.")
        else:
            print(f"Aviso: El empleado '{obj_empleado.nombre}' ya estaba asignado a ese proyecto.")
        
        return True

    except Empleado.DoesNotExist:
        print(f"Error: Empleado con DNI {dni_empleado} no existe.")
        return False
    except Proyecto.DoesNotExist:
        print(f"Error: Proyecto con ID {id_proyecto} no existe.")
        return False
    except Exception as e:
        print(f"Error inesperado al asignar empleado: {e}")
        return False
    finally:
        if not db.is_closed():
            db.close()

if __name__ == "__main__":
    try:
        crear_tablas()
    except Exception as e:
        print(f"Error al crear las tablas: {e}")
        exit(1)
    print("Iniciando script de inserción...")
    
    insertar_clientes_bulk()
    insertar_empleados_bulk()

    insertar_proyecto(
        titulo="Rediseño Web TechNova",
        desc="Actualización completa del portal corporativo.",
        f_inicio="2024-01-15",
        f_fin="2024-06-30",
        presupuesto=25000.0,
        dni_cliente="E19329838",
        dni_jefe="17520760G"
    )
    
    # Falla: fallan por las fechas con el ID 1 (17520760G)
    insertar_proyecto(
        titulo="Infraestructura Cloud",
        desc="Migración de servidores a la nube.",
        f_inicio="2024-02-10", 
        f_fin="2024-08-15",
        presupuesto=45000.0,
        dni_cliente="H10703833",
        dni_jefe="17520760G"
    )
    
    # Funciona: no interfieren las fechas
    insertar_proyecto(
        titulo="Proyecto Post-Verano",
        desc="Desarrollo tras vacaciones.",
        f_inicio="2024-09-01", 
        f_fin="2024-12-31",
        presupuesto=30000.0,
        dni_cliente="E17889122",
        dni_jefe="17520760G"
    )
    
    # Falla: El "jefe" no cumple ('jefe' = True)
    insertar_proyecto(
        titulo="Sistema ERP InnovaSoft",
        desc="Implementación de un ERP personalizado.",
        f_inicio="2024-03-01",
        f_fin="2024-10-01",
        presupuesto=60000.0,
        dni_cliente="H65740417",
        dni_jefe="87744401E"
    )
    
    asignar_empleado_a_proyecto(dni_empleado="87744401E", id_proyecto=1)
    asignar_empleado_a_proyecto(dni_empleado="60657870Q", id_proyecto=1)
    asignar_empleado_a_proyecto(dni_empleado="13769630J", id_proyecto=1)
    
    print("\nProceso de inserción finalizado")