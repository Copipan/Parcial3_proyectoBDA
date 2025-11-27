from flask import Blueprint, request, jsonify
from extensions import get_driver
import json
from datetime import datetime

articulos_bp = Blueprint('articulos', __name__)

def serialize_neo4j_data(data):
    """Función helper para serializar datos de Neo4j a JSON"""
    if isinstance(data, dict):
        return {key: serialize_neo4j_data(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [serialize_neo4j_data(item) for item in data]
    elif hasattr(data, 'iso_format'):
        # Para objetos de fecha de Neo4j
        return data.iso_format()
    elif hasattr(data, 'to_native'):
        # Para otros tipos de Neo4j
        return data.to_native()
    else:
        return data

# GET /api/articulos
@articulos_bp.route('', methods=['GET'])
def get_articulos():
    driver = get_driver()
    
    # Query para obtener artículos con información completa
    query = """
    MATCH (a:Article)
    OPTIONAL MATCH (author:User)-[:WROTE]->(a)
    OPTIONAL MATCH (a)-[:TAGGED_WITH]->(tag:Tag)
    OPTIONAL MATCH (a)-[:IN_CATEGORY]->(cat:Category)
    RETURN a.id as articulo_id,
           a.title as titulo,
           a.content as content,
           a.createdAt as created_at,
           author.id as user_id,
           author.name as user_name,
           COLLECT(DISTINCT {tname: tag.name}) as tags,
           COLLECT(DISTINCT {cname: cat.name}) as categories
    ORDER BY a.createdAt DESC
    """
    
    try:
        with driver.session() as session:
            result = session.run(query)
            articulos = []
            
            for record in result:
                # Convertir el registro a diccionario y serializar
                articulo_data = dict(record)
                articulo_serializado = serialize_neo4j_data(articulo_data)
                
                articulos.append({
                    "articulo_id": articulo_serializado["articulo_id"],
                    "user_id": articulo_serializado["user_id"],
                    "user_name": articulo_serializado["user_name"],
                    "titulo": articulo_serializado["titulo"],
                    "content": articulo_serializado["content"],
                    "tags": articulo_serializado["tags"] or [],
                    "categories": articulo_serializado["categories"] or [],
                    "created_at": articulo_serializado["created_at"]
                })
            
            return jsonify(articulos)
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# POST /api/articulos
@articulos_bp.route('', methods=['POST'])
def create_articulo():
    data = request.get_json()
    driver = get_driver()
    
    try:
        # Validar datos requeridos
        if not data.get('titulo') or not data.get('article_text'):
            return jsonify({"error": "Faltan campos requeridos: titulo y article_text"}), 400
        
        with driver.session() as session:
            # Obtener el siguiente ID para el artículo
            id_query = "MATCH (a:Article) RETURN coalesce(max(a.id), 0) + 1 as nextId"
            id_result = session.run(id_query).single()
            new_id = id_result["nextId"]
            
            # Crear el artículo
            create_query = """
            CREATE (a:Article {
                id: $id,
                title: $title,
                content: $content,
                createdAt: datetime()
            })
            WITH a
            MATCH (author:User {id: $author_id})
            MERGE (author)-[:WROTE]->(a)
            RETURN a
            """
            
            # Ejecutar creación del artículo
            result = session.run(create_query, 
                       id=new_id,
                       title=data.get('titulo'),
                       content=data.get('article_text'),
                       author_id=data.get('user_id', 0))
            
            if not result.single():
                return jsonify({"error": "No se pudo crear el artículo"}), 500
            
            # Conectar tags si se proporcionan
            tags = data.get('tags', [])
            if tags:
                tag_query = """
                MATCH (a:Article {id: $article_id})
                UNWIND $tags AS tag_id
                MATCH (t:Tag {id: tag_id})
                MERGE (a)-[:TAGGED_WITH]->(t)
                """
                session.run(tag_query, article_id=new_id, tags=tags)
            
            # Conectar categorías si se proporcionan
            categories = data.get('categories', [])
            if categories:
                cat_query = """
                MATCH (a:Article {id: $article_id})
                UNWIND $categories AS cat_id
                MATCH (c:Category {id: cat_id})
                MERGE (a)-[:IN_CATEGORY]->(c)
                """
                session.run(cat_query, article_id=new_id, categories=categories)
            
            # Recuperar el artículo creado con toda la información
            get_query = """
            MATCH (a:Article {id: $id})
            OPTIONAL MATCH (author:User)-[:WROTE]->(a)
            OPTIONAL MATCH (a)-[:TAGGED_WITH]->(tag:Tag)
            OPTIONAL MATCH (a)-[:IN_CATEGORY]->(cat:Category)
            RETURN a.id as articulo_id,
                   a.title as titulo,
                   a.content as content,
                   a.createdAt as created_at,
                   author.id as user_id,
                   author.name as user_name,
                   COLLECT(DISTINCT {tname: tag.name}) as tags,
                   COLLECT(DISTINCT {cname: cat.name}) as categories
            """
            
            result = session.run(get_query, id=new_id).single()
            
            if result:
                articulo_data = dict(result)
                articulo_serializado = serialize_neo4j_data(articulo_data)
                
                new_article = {
                    "articulo_id": articulo_serializado["articulo_id"],
                    "user_id": articulo_serializado["user_id"],
                    "user_name": articulo_serializado["user_name"],
                    "titulo": articulo_serializado["titulo"],
                    "content": articulo_serializado["content"],
                    "tags": articulo_serializado["tags"] or [],
                    "categories": articulo_serializado["categories"] or [],
                    "created_at": articulo_serializado["created_at"]
                }
                
                return jsonify(new_article), 201
            else:
                return jsonify({"error": "No se pudo recuperar el artículo creado"}), 500
                
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# DELETE /api/articulos/<id>
@articulos_bp.route('/<int:id>', methods=['DELETE'])
def delete_articulo(id):
    driver = get_driver()
    
    try:
        with driver.session() as session:
            # Eliminar el artículo y todas sus relaciones
            query = """
            MATCH (a:Article {id: $id})
            OPTIONAL MATCH (c:Comment)-[:ON_ARTICLE]->(a)
            DETACH DELETE a, c
            """
            
            result = session.run(query, id=id)
            summary = result.consume()
            
            if summary.counters.nodes_deleted == 0:
                return jsonify({"error": "Artículo no encontrado"}), 404
                
            return "", 204
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# GET /api/articulos/<id>/comentarios
@articulos_bp.route('/<int:id>/comentarios', methods=['GET'])
def get_comentarios_articulo(id):
    driver = get_driver()
    
    try:
        query = """
        MATCH (c:Comment)-[:ON_ARTICLE]->(a:Article {id: $id})
        MATCH (u:User)-[:POSTED]->(c)
        RETURN c.id as _id,
               c.text as comment,
               c.createdAt as created_at,
               u.name as user_name,
               u.id as user_id
        ORDER BY c.createdAt DESC
        """
        
        with driver.session() as session:
            result = session.run(query, id=id)
            comentarios = []
            
            for record in result:
                comentario_data = dict(record)
                comentario_serializado = serialize_neo4j_data(comentario_data)
                
                comentarios.append({
                    "_id": comentario_serializado["_id"],
                    "comment": comentario_serializado["comment"],
                    "created_at": comentario_serializado["created_at"],
                    "user_name": comentario_serializado["user_name"],
                    "user_id": comentario_serializado["user_id"]
                })
            
            return jsonify({
                "articulo_id": id,
                "count": len(comentarios),
                "comentarios": comentarios
            })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500