from flask import Blueprint, request, jsonify
from extensions import get_driver
from datetime import datetime

comentarios_bp = Blueprint('comentarios', __name__)

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

# GET /api/comentarios
@comentarios_bp.route('', methods=['GET'])
def get_comentarios():
    driver = get_driver()
    
    # Query para obtener comentarios con información de usuario y artículo
    query = """
    MATCH (c:Comment)-[:ON_ARTICLE]->(a:Article)
    MATCH (u:User)-[:POSTED]->(c)
    RETURN c.id as _id,
           c.text as comment,
           c.createdAt as created_at,
           u.name as user_name,
           u.id as user_id,
           a.title as article_title,
           a.id as article_id
    ORDER BY c.createdAt DESC
    """
    
    try:
        with driver.session() as session:
            result = session.run(query)
            comentarios = []
            
            for record in result:
                comentario_data = dict(record)
                comentario_serializado = serialize_neo4j_data(comentario_data)
                
                comentarios.append({
                    "_id": comentario_serializado["_id"],
                    "comment": comentario_serializado["comment"],
                    "created_at": comentario_serializado["created_at"],
                    "user_name": comentario_serializado["user_name"],
                    "user_id": comentario_serializado["user_id"],
                    "article_title": comentario_serializado["article_title"],
                    "article_id": comentario_serializado["article_id"]
                })
            
            return jsonify(comentarios)
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# POST /api/comentarios
@comentarios_bp.route('', methods=['POST'])
def create_comentario():
    data = request.get_json()
    driver = get_driver()
    
    try:
        # Validar campos requeridos
        if not data.get('articulo_id') or not data.get('texto_com'):
            return jsonify({"error": "Faltan campos requeridos: articulo_id y texto_com"}), 400
        
        with driver.session() as session:
            # Obtener el siguiente ID para el comentario
            id_query = "MATCH (c:Comment) RETURN coalesce(max(c.id), 0) + 1 as nextId"
            id_result = session.run(id_query).single()
            new_id = id_result["nextId"]
            
            # Verificar que el artículo existe
            article_check = "MATCH (a:Article {id: $article_id}) RETURN a"
            article_result = session.run(article_check, article_id=data.get('articulo_id')).single()
            
            if not article_result:
                return jsonify({"error": "El artículo especificado no existe"}), 404
            
            # Verificar que el usuario existe
            user_check = "MATCH (u:User {id: $user_id}) RETURN u"
            user_result = session.run(user_check, user_id=data.get('user_id', 0)).single()
            
            if not user_result:
                return jsonify({"error": "El usuario especificado no existe"}), 404
            
            # Crear el comentario
            create_query = """
            CREATE (c:Comment {
                id: $id,
                text: $text,
                createdAt: datetime()
            })
            WITH c
            MATCH (u:User {id: $user_id})
            MATCH (a:Article {id: $article_id})
            MERGE (u)-[:POSTED]->(c)
            MERGE (c)-[:ON_ARTICLE]->(a)
            RETURN c
            """
            
            result = session.run(create_query, 
                               id=new_id,
                               text=data.get('texto_com'),
                               user_id=data.get('user_id', 0),
                               article_id=data.get('articulo_id'))
            
            if result.single():
                # Recuperar el comentario creado con toda la información
                get_query = """
                MATCH (c:Comment {id: $id})-[:ON_ARTICLE]->(a:Article)
                MATCH (u:User)-[:POSTED]->(c)
                RETURN c.id as _id,
                       c.text as comment,
                       c.createdAt as created_at,
                       u.name as user_name,
                       u.id as user_id,
                       a.title as article_title,
                       a.id as article_id
                """
                
                comment_result = session.run(get_query, id=new_id).single()
                
                if comment_result:
                    comment_data = dict(comment_result)
                    comment_serializado = serialize_neo4j_data(comment_data)
                    
                    new_comment = {
                        "_id": comment_serializado["_id"],
                        "comment": comment_serializado["comment"],
                        "created_at": comment_serializado["created_at"],
                        "user_name": comment_serializado["user_name"],
                        "user_id": comment_serializado["user_id"],
                        "article_title": comment_serializado["article_title"],
                        "article_id": comment_serializado["article_id"]
                    }
                    
                    return jsonify(new_comment), 201
                else:
                    return jsonify({"error": "No se pudo recuperar el comentario creado"}), 500
            else:
                return jsonify({"error": "No se pudo crear el comentario"}), 500
                
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# DELETE /api/comentarios/<id>
@comentarios_bp.route('/<int:id>', methods=['DELETE'])
def delete_comentario(id):
    driver = get_driver()
    
    try:
        with driver.session() as session:
            # Eliminar el comentario y todas sus relaciones
            query = """
            MATCH (c:Comment {id: $id})
            DETACH DELETE c
            """
            
            result = session.run(query, id=id)
            summary = result.consume()
            
            if summary.counters.nodes_deleted == 0:
                return jsonify({"error": "Comentario no encontrado"}), 404
                
            return "", 204
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500