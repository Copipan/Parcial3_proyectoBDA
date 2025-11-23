from flask import Blueprint, jsonify, request
from extensions import get_driver
import urllib.parse

usuarios_bp = Blueprint('usuarios_bp', __name__)

# GET /api/usuarios
@usuarios_bp.route('', methods=['GET'], strict_slashes=False)
def get_usuarios():
    driver = get_driver()
    
    # Query: Busca todos los nodos con la etiqueta User y retorna el nodo completo 'u'
    query = "MATCH (u:User) RETURN u"
    
    try:
        with driver.session() as session:
            result = session.run(query)
            
            # Transformación:
            # 1. Iteramos sobre el cursor (result)
            # 2. record["u"] nos da el Nodo
            # 3. dict(record["u"]) convierte las propiedades del nodo a un diccionario de Python
            usuarios = [dict(record["u"]) for record in result]
            
            return jsonify(usuarios)
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# POST /api/usuarios
@usuarios_bp.route('', methods=['POST'], strict_slashes=False)
def create_usuario():
    data = request.get_json()
    # 1. Validar datos de entrada
    if 'user_name' not in data or 'email' not in data:
        return jsonify({"error": "Faltan los campos 'name' y 'email'"}), 400
    print(data)
    driver = get_driver()
    email = data['email']
    name = data['user_name']
    
    try:
        with driver.session() as session:
            
            # 2. Verificar si el email ya existe
            # Usamos COUNT para ser más eficientes que traer todo el nodo
            check_query = "MATCH (u:User {email: $email}) RETURN count(u) as existe"
            check_result = session.run(check_query, email=email).single()
            
            if check_result["existe"] > 0:
                return jsonify({"error": "El email ya existe"}), 409

            # 3. Crear el usuario
            # 3.1 Buscamos el ID más alto actual
            # COALESCE es para que si no hay tags (devuelve null), use 0 por defecto.
            id_query = "MATCH (t:User) RETURN coalesce(max(t.id), 0) + 1 as nextId"
            id_result = session.run(id_query).single()
            
            # Este es tu nuevo ID (ej: si el max era 10, ahora new_id es 11)
            new_id = id_result["nextId"]
            create_query = """
            CREATE (u:User {
                id: $id, 
                name: $name, 
                email: $email
            }) 
            RETURN u
            """
            
            # Ejecutamos pasando las variables para evitar inyección
            insert_result = session.run(create_query, id=new_id, name=name, email=email).single()
            
            if insert_result:
                # Convertimos el nodo creado a diccionario para responder
                new_user = dict(insert_result["u"])
                return jsonify(new_user), 201
            else:
                return jsonify({"error": "No se pudo crear el usuario"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# PUT /api/usuarios/<originalEmail>
@usuarios_bp.route('/<string:originalEmail>', methods=['PUT'])
def update_usuario(originalEmail):
    try:
        data = request.get_json()
        # Decodificar el email de la URL (ej: carlos%40gmail.com -> carlos@gmail.com)
        decoded_email = urllib.parse.unquote(originalEmail)
        print(data)
        updates = {}
        # Mantenemos tu lógica de flags booleanas
        if data.get('name_bool') == 1:
            updates["name"] = data.get('user_name')
        if data.get('email_bool') == 1:
            updates["email"] = data.get('email')

        if not updates:
            return jsonify({"error": "No hay campos para actualizar"}), 400
            
        driver = get_driver()
        
        # Cypher Query:
        # 1. Buscamos al usuario por su email ORIGINAL.
        # 2. SET u += $props: Esto actualiza SOLO las propiedades que vienen en el diccionario.
        #    Si updates trae {"name": "Nuevo"}, solo cambia el nombre.
        #    Si trae {"email": "nuevo@x.com"}, cambia el email del nodo.
        query = """
        MATCH (u:User {email: $original_email})
        SET u += $props
        RETURN u
        """
        
        with driver.session() as session:
            result = session.run(query, original_email=decoded_email, props=updates)
            
            # Intentamos obtener el primer resultado
            record = result.single()
            
            if not record:
                # Si record es None, significa que el MATCH no encontró al usuario
                return jsonify({"error": "Usuario no encontrado"}), 404
            
            return jsonify({"message": "Usuario actualizado"})
            
    except Exception as e:
        return jsonify(error=str(e)), 500


# DELETE /api/usuarios/<email>
@usuarios_bp.route('/<string:email>', methods=['DELETE'])
def delete_usuario(email):
    try:
        decoded_email = urllib.parse.unquote(email)
        driver = get_driver()
        
        # Cypher Query:
        # DETACH DELETE: "Desconecta y Borra".
        # Si el usuario escribió comentarios o artículos, esas FLECHAS se borran,
        # y luego se borra el nodo Usuario.
        # (Nota: Los artículos y comentarios quedan huérfanos, no se borran ellos, solo el autor).
        query = """
        MATCH (u:User {email: $email})
        DETACH DELETE u
        """
        
        with driver.session() as session:
            result = session.run(query, email=decoded_email)
            
            # ¿Cómo sabemos si borró algo?
            # Consultamos las estadísticas de la transacción (summary counters)
            summary = result.consume()
            nodes_deleted = summary.counters.nodes_deleted
            
            if nodes_deleted == 0:
                return jsonify({"error": "Usuario no encontrado"}), 404
            
            return "", 204 # 204 No Content (éxito)
            
    except Exception as e:
        return jsonify(error=str(e)), 500