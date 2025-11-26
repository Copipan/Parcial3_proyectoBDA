from flask import Blueprint, request, jsonify
from extensions import get_driver
import urllib.parse

categorias_bp = Blueprint('categorias', __name__)

def serialize_neo4j_data(data):
    """Función helper para serializar datos de Neo4j a JSON"""
    if isinstance(data, dict):
        return {key: serialize_neo4j_data(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [serialize_neo4j_data(item) for item in data]
    elif hasattr(data, 'iso_format'):
        return data.iso_format()
    elif hasattr(data, 'to_native'):
        return data.to_native()
    else:
        return data

# GET /api/categorias
@categorias_bp.route('', methods=['GET'])
def get_categorias():
    driver = get_driver()
    query = """
    MATCH (c:Category) 
    RETURN c.id as _id, c.name as category_name
    ORDER BY c.name
    """
    
    try:
        with driver.session() as session:
            result = session.run(query)
            categorias = []
            
            for record in result:
                categoria_data = dict(record)
                categoria_serializada = serialize_neo4j_data(categoria_data)
                
                categorias.append({
                    "_id": categoria_serializada["_id"],
                    "category_name": categoria_serializada["category_name"],
                    "url_cat": f"/categoria/{categoria_serializada['category_name'].lower().replace(' ', '-')}"
                })
            
            return jsonify(categorias)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# GET /api/categorias/ids
@categorias_bp.route('/ids', methods=['GET'])
def get_categorias_with_ids():
    driver = get_driver()
    query = "MATCH (c:Category) RETURN c.id as _id, c.name as category_name ORDER BY c.name"
    
    try:
        with driver.session() as session:
            result = session.run(query)
            categorias = []
            
            for record in result:
                categoria_data = dict(record)
                categoria_serializada = serialize_neo4j_data(categoria_data)
                categorias.append({
                    "_id": categoria_serializada["_id"],
                    "category_name": categoria_serializada["category_name"]
                })
                
            return jsonify(categorias)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# POST /api/categorias
@categorias_bp.route('', methods=['POST'])
def create_categoria():
    try:
        data = request.get_json()
        
        # Validar campos
        if 'category_name' not in data:
            return jsonify({"error": "Falta el campo 'category_name'"}), 400
        
        driver = get_driver()
        
        with driver.session() as session:
            # Verificar duplicados
            check_query = "MATCH (c:Category {name: $name}) RETURN count(c) as existe"
            check_result = session.run(check_query, name=data['category_name']).single()
            
            if check_result["existe"] > 0:
                return jsonify({"error": "Ese nombre de categoría ya existe"}), 409

            # Obtener siguiente ID
            id_query = "MATCH (c:Category) RETURN coalesce(max(c.id), 0) + 1 as nextId"
            id_result = session.run(id_query).single()
            new_id = id_result["nextId"]

            # Crear categoría
            create_query = """
            CREATE (c:Category {
                id: $id,
                name: $name
            }) 
            RETURN c
            """
            
            insert_result = session.run(create_query, id=new_id, name=data['category_name']).single()
            
            if insert_result:
                category_node = insert_result["c"]
                category_data = dict(category_node)
                category_serializada = serialize_neo4j_data(category_data)
                
                new_cat = {
                    '_id': category_serializada["id"],
                    'category_name': category_serializada["name"],
                    'url_cat': f"/categoria/{category_serializada['name'].lower().replace(' ', '-')}"
                }
                return jsonify(new_cat), 201
            else:
                return jsonify({"error": "No se pudo crear la categoría"}), 500
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# PUT /api/categorias/<originalName>
@categorias_bp.route('/<string:originalName>', methods=['PUT'])
def update_categoria(originalName):
    try:
        data = request.get_json()
        decoded_name = urllib.parse.unquote(originalName)
        
        # Validar campos
        if 'category_name' not in data:
            return jsonify({"error": "Falta el campo 'category_name'"}), 400

        driver = get_driver()
        
        query = """
        MATCH (c:Category {name: $original_name})
        SET c.name = $new_name
        RETURN c
        """
        
        with driver.session() as session:
            result = session.run(query, original_name=decoded_name, new_name=data['category_name'])
            record = result.single()
            
            if not record:
                return jsonify({"error": "Categoría no encontrada"}), 404
            
            return jsonify({"message": "Categoría actualizada"})
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# DELETE /api/categorias/<name>
@categorias_bp.route('/<string:name>', methods=['DELETE'])
def delete_categoria(name):
    try:
        decoded_name = urllib.parse.unquote(name)
        driver = get_driver()
        
        query = """
        MATCH (c:Category {name: $name})
        DETACH DELETE c
        """
        
        with driver.session() as session:
            result = session.run(query, name=decoded_name)
            summary = result.consume()
            
            if summary.counters.nodes_deleted == 0:
                return jsonify({"error": "Categoría no encontrada"}), 404
            
            return "", 204
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

