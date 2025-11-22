from flask import Blueprint, request, jsonify
from extensions import mongo
from bson import json_util
import json
from bson.objectid import ObjectId

categoria_articulos_bp = Blueprint('categoria_articulos', __name__)

# GET /api/categoria/<cname>/articulos
@categoria_articulos_bp.route('/<string:cname>/articulos', methods=['GET'])
def get_articulos_por_categoria(cname):
    try:
        # Primero buscar la categoría por nombre para obtener su ID
        categoria = mongo.db.categories.find_one({"cname": cname})
        
        if not categoria:
            return jsonify({
                "message": f"No se encontró la categoría '{cname}'",
                "data": []
            }), 404
        
        categoria_id = categoria['_id']  # Este es el ID numérico (1)
        
        print(f"Buscando artículos con categoría ID: {categoria_id}, tipo: {type(categoria_id)}")
        
        # Buscar artículos que tengan este ID numérico en su array categories
        articulos = list(mongo.db.articles.find({
            "categories": categoria_id  # Buscar directamente el número 1
        }))
        
        print(f"Artículos encontrados: {len(articulos)}")
        
        if not articulos:
            return jsonify({
                "message": f"No se encontraron artículos para la categoría '{cname}'",
                "data": []
            }), 404
        
        # Transformar los datos para el frontend
        articulos_transformados = []
        for articulo in articulos:
            print(f"Procesando artículo: {articulo['title']}")
            print(f"Categorías del artículo: {articulo.get('categories', [])}")
            
            # Obtener información del autor (author_id también parece ser numérico)
            autor = mongo.db.users.find_one({"_id": articulo["author_id"]})
            autor_name = autor["name"] if autor else "Autor desconocido"
            
            # Obtener nombres de las categorías en lugar de IDs numéricos
            categorias_nombres = []
            for cat_id in articulo.get("categories", []):
                try:
                    # Buscar la categoría por su ID numérico
                    cat_obj = mongo.db.categories.find_one({"_id": cat_id})
                    if cat_obj:
                        categorias_nombres.append(cat_obj["cname"])
                        print(f"ID categoría {cat_id} -> nombre: {cat_obj['cname']}")
                except Exception as e:
                    print(f"Error al buscar categoría ID {cat_id}: {e}")
                    continue
            
            # Obtener nombres de los tags si existen (también parecen ser numéricos)
            tags_nombres = []
            for tag_id in articulo.get("tags", []):
                try:
                    tag_obj = mongo.db.tags.find_one({"_id": tag_id})
                    if tag_obj:
                        tags_nombres.append(tag_obj["tname"])
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
            "categoria": cname,
            "categoria_id": str(categoria_id),
            "count": len(articulos_transformados),
            "articulos": articulos_transformados
        }))
        
    except Exception as e:
        print(f"Error general: {e}")
        return jsonify({"error": str(e)}), 500