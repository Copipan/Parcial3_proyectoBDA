from flask import Blueprint, request, jsonify
from extensions import get_driver
import json

tag_articulos_bp = Blueprint('tag_articulos', __name__)

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

# GET /api/tag/<tname>/articulos
@tag_articulos_bp.route('/<string:tname>/articulos', methods=['GET'])
def get_articulos_por_tag(tname):
    driver = get_driver()
    
    query = """
    MATCH (a:Article)-[:TAGGED_WITH]->(t:Tag {name: $tname})
    OPTIONAL MATCH (author:User)-[:WROTE]->(a)
    OPTIONAL MATCH (a)-[:TAGGED_WITH]->(tag:Tag)
    OPTIONAL MATCH (a)-[:IN_CATEGORY]->(cat:Category)
    RETURN a.id as _id,
           a.title as title,
           a.content as content,
           a.createdAt as created_at,
           author.name as author_name,
           author.id as author_id,
           COLLECT(DISTINCT tag.name) as tags,
           COLLECT(DISTINCT cat.name) as categories
    ORDER BY a.createdAt DESC
    """
    
    try:
        with driver.session() as session:
            result = session.run(query, tname=tname)
            articulos = []
            
            for record in result:
                articulo_data = dict(record)
                articulo_serializado = serialize_neo4j_data(articulo_data)
                
                # Crear excerpt del contenido
                contenido = articulo_serializado.get("content", "")
                excerpt = contenido[:150] + "..." if len(contenido) > 150 else contenido
                
                articulos.append({
                    "_id": articulo_serializado["_id"],
                    "title": articulo_serializado["title"],
                    "content": contenido,
                    "author_name": articulo_serializado.get("author_name", "Autor desconocido"),
                    "author_id": articulo_serializado.get("author_id"),
                    "tags": articulo_serializado.get("tags", []),
                    "categories": articulo_serializado.get("categories", []),
                    "created_at": articulo_serializado["created_at"],
                    "excerpt": excerpt
                })
            
            return jsonify({
                "tag": tname,
                "count": len(articulos),
                "articulos": articulos
            })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500