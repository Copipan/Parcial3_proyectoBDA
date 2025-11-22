from flask import Blueprint, request, jsonify
from extensions import mongo
from bson import json_util
import json
from bson.objectid import ObjectId

tag_articulos_bp = Blueprint('tag_articulos', __name__)

# GET /api/tag/<tname>/articulos
@tag_articulos_bp.route('/<string:tname>/articulos', methods=['GET'])
def get_articulos_por_tag(tname):
    try:
        # Primero buscar el tag por nombre para obtener su ID
        tag = mongo.db.tags.find_one({"tname": tname})
        
        if not tag:
            return jsonify({
                "message": f"No se encontró el tag '{tname}'",
                "data": []
            }), 404
        
        tag_id = tag['_id']  # ID numérico del tag
        
        print(f"Buscando artículos con tag ID: {tag_id}, tipo: {type(tag_id)}")
        
        # Buscar artículos que tengan este ID numérico en su array tags
        articulos = list(mongo.db.articles.find({
            "tags": tag_id  # Buscar directamente el número (ID del tag)
        }))
        
        print(f"Artículos encontrados: {len(articulos)}")
        
        if not articulos:
            return jsonify({
                "message": f"No se encontraron artículos para el tag '{tname}'",
                "data": []
            }), 404
        
        # Transformar los datos para el frontend
        articulos_transformados = []
        for articulo in articulos:
            print(f"Procesando artículo: {articulo['title']}")
            print(f"Tags del artículo: {articulo.get('tags', [])}")
            
            # Obtener información del autor
            autor = mongo.db.users.find_one({"_id": articulo["author_id"]})
            autor_name = autor["name"] if autor else "Autor desconocido"
            
            # Obtener nombres de los tags en lugar de IDs numéricos
            tags_nombres = []
            for tag_id in articulo.get("tags", []):
                try:
                    # Buscar el tag por su ID numérico
                    tag_obj = mongo.db.tags.find_one({"_id": tag_id})
                    if tag_obj:
                        tags_nombres.append(tag_obj["tname"])
                        print(f"ID tag {tag_id} -> nombre: {tag_obj['tname']}")
                except Exception as e:
                    print(f"Error al buscar tag ID {tag_id}: {e}")
                    continue
            
            # Obtener nombres de las categorías (también parecen ser numéricas)
            categorias_nombres = []
            for cat_id in articulo.get("categories", []):
                try:
                    cat_obj = mongo.db.categories.find_one({"_id": cat_id})
                    if cat_obj:
                        categorias_nombres.append(cat_obj["cname"])
                except:
                    continue
            
            # Crear excerpt del contenido
            contenido = articulo.get("content", "")
            excerpt = contenido[:150] + "..." if len(contenido) > 150 else contenido
            
            articulos_transformados.append({
                "_id": str(articulo["_id"]),
                "title": articulo["title"],
                "content": contenido,
                "author_name": autor_name,
                "author_id": str(articulo["author_id"]),
                "tags": tags_nombres,
                "categories": categorias_nombres,
                "created_at": articulo.get("created_at", ""),
                "excerpt": excerpt
            })
        
        return json.loads(json_util.dumps({
            "tag": tname,
            "tag_id": str(tag_id),
            "count": len(articulos_transformados),
            "articulos": articulos_transformados
        }))
        
    except Exception as e:
        print(f"Error general: {e}")
        return jsonify({"error": str(e)}), 500