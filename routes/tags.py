from flask import Blueprint, jsonify, request
from extensions import get_driver
import urllib.parse

tags_bp = Blueprint('tags', __name__)

# GET /api/tags
@tags_bp.route('', methods=['GET'], strict_slashes=False)
def get_tags():
    driver = get_driver()
    # Recuperamos todos los nodos con la etiqueta Tag
    query = "MATCH (t:Tag) RETURN t"
    
    try:
        with driver.session() as session:
            result = session.run(query)
            
            tags = []
            for record in result:
                # Convertimos el nodo a diccionario
                tag_data = dict(record["t"])
                tags.append(tag_data)
            return jsonify(tags)
            
    except Exception as e:
        return jsonify(error=str(e)), 500

# POST /api/tags
@tags_bp.route('', methods=['POST'], strict_slashes=False)
def create_tag():
    data = request.get_json() # Espera: { tname, tagurl }
    print(data)
    # 1. Validar campos
    if 'name' not in data or 'url' not in data:
        return jsonify({"error": "Faltan los campos 'name' y 'url'"}), 400
    
    driver = get_driver()
    name = data['name']
    url = data['url']
    
    try:
        with driver.session() as session:
            # 2. Verificar duplicados
            # Buscamos si existe un Tag con ese tname
            check_query = "MATCH (t:Tag {name: $name}) RETURN count(t) as existe"
            check_result = session.run(check_query, name=name).single()
            
            if check_result["existe"] > 0:
                return jsonify({"error": "Ese 'name' de tag ya existe"}), 409

            # 3. Insertar
            # 3.1 Buscamos el ID más alto actual
            # COALESCE es para que si no hay tags (devuelve null), use 0 por defecto.
            id_query = "MATCH (t:Tag) RETURN coalesce(max(t.id), 0) + 1 as nextId"
            id_result = session.run(id_query).single()
            
            # Este es tu nuevo ID (ej: si el max era 10, ahora new_id es 11)
            new_id = id_result["nextId"]
            # Nota: Guardamos las propiedades 'tname' y 'tagurl' tal cual las pide el frontend.
            create_query = """
            CREATE (t:Tag {
                id: $id,
                name: $name, 
                url: $url
            }) 
            RETURN t
            """
            
            insert_result = session.run(create_query, id=new_id, name=name, url=url).single()
            
            if insert_result:
                new_tag = dict(insert_result["t"])
                return jsonify(new_tag), 201
            else:
                return jsonify({"error": "No se pudo crear el tag"}), 500
                
    except Exception as e:
        return jsonify(error=str(e)), 500

# PUT /api/tags/<tname>
@tags_bp.route('/<string:name>', methods=['PUT'])
def update_tag(name):
    try:
        data = request.get_json()
        decoded_name = urllib.parse.unquote(name)
        
        # 1. Validar campos (Igual que en Mongo)
        if 'name' not in data or 'url' not in data:
            return jsonify({"error": "Faltan los campos 'name' y 'url'"}), 400

        driver = get_driver()
        
        # 2. Actualizar
        # Buscamos por el nombre ORIGINAL (decoded_name).
        # Actualizamos con los nuevos datos (data).
        # Si data['tname'] es diferente al original, esto renombra el tag efectivamente.
        query = """
        MATCH (t:Tag {name: $original_name})
        SET t += $props
        RETURN t
        """
        
        with driver.session() as session:
            result = session.run(query, original_name=decoded_name, props=data)
            record = result.single()
            
            if not record:
                return jsonify({"error": "Tag no encontrado"}), 404
            
            return jsonify({"message": "Tag actualizado"})
            
    except Exception as e:
        # Nota: Si intentas renombrar a un tag que ya existe y tienes UNIQUE CONSTRAINTS,
        # esto lanzará un error que caerá aquí.
        return jsonify(error=str(e)), 500

# DELETE /api/tags/<tname>
@tags_bp.route('/<string:tname>', methods=['DELETE'])
def delete_tag(tname):
    try:
        decoded_name = urllib.parse.unquote(tname)
        driver = get_driver()
        print(decoded_name)
        
        # 3. Eliminar
        query = """
        MATCH (t:Tag {name: $name})
        DETACH DELETE t
        """
        
        with driver.session() as session:
            result = session.run(query, name=decoded_name)
            summary = result.consume()
            
            if summary.counters.nodes_deleted == 0:
                return jsonify({"error": "Tag no encontrado"}), 404
            
            return "", 204 # Éxito sin contenido
            
    except Exception as e:
        return jsonify(error=str(e)), 500

# GET /api/tags/ids
@tags_bp.route('/ids', methods=['GET'])
def get_tags_with_ids():
    driver = get_driver()
    query = "MATCH (t:Tag) RETURN t.id as _id, t.name as tname ORDER BY t.name"
    
    try:
        with driver.session() as session:
            result = session.run(query)
            tags = []
            
            for record in result:
                tag_data = dict(record)
                # Asegurarnos de que estamos serializando correctamente
                tag_serializado = {
                    "_id": tag_data.get("_id"),
                    "tname": tag_data.get("tname")
                }
                tags.append(tag_serializado)
                
            print(f"Tags encontrados: {tags}")  # Debug
            return jsonify(tags)
    except Exception as e:
        print(f"Error en /tags/ids: {e}")  # Debug
        return jsonify({"error": str(e)}), 500

# PUT /api/tags/<tname> (Usamos 'tname' para consistencia)
# @tags_bp.route('/<string:tname>', methods=['PUT'])
# def update_tag(tname):
#     try:
#         data = request.get_json() # Espera: { tname, tagurl }
#         decoded_name = urllib.parse.unquote(tname)
        
#         # Validar campos
#         if 'tname' not in data or 'tagurl' not in data:
#             return jsonify({"error": "Faltan los campos 'tname' y 'tagurl'"}), 400

#         # --- LÓGICA CORREGIDA ---
#         # Busca por 'tname' (de scriptbasemongo.txt)
#         result = mongo.db.tags.update_one(
#             {"tname": decoded_name},
#             {"$set": data}
#         )
        
#         if result.matched_count == 0:
#             return jsonify({"error": "Tag no encontrado"}), 404
            
#         return jsonify({"message": "Tag actualizado"})
        
#     except Exception as e:
#         return jsonify(error=str(e)), 500

# # DELETE /api/tags/<tname>
# @tags_bp.route('/<string:tname>', methods=['DELETE'])
# def delete_tag(tname):
#     try:
#         decoded_name = urllib.parse.unquote(tname)
        
#         # --- LÓGICA CORREGIDA ---
#         # Busca por 'tname' (de scriptbasemongo.txt)
#         result = mongo.db.tags.delete_one({"tname": decoded_name})
        
#         if result.deleted_count == 0:
#             return jsonify({"error": "Tag no encontrado"}), 404
            
#         return "", 204 # Éxito sin contenido
        
#     except Exception as e:
#         return jsonify(error=str(e)), 500