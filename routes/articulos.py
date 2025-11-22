from flask import Blueprint, request, jsonify
from extensions import init_neo4j, close_driver
from bson import json_util
import json
import datetime

articulos_bp = Blueprint('articulos', __name__)

# GET /api/articulos
@articulos_bp.route('', methods=['GET'])
def get_articulos():
    try:
        # Pipeline mejorado con información de tags y categorías
        pipeline = [
            {
                '$lookup': {
                    'from': 'users',
                    'localField': 'author_id',
                    'foreignField': '_id',
                    'as': 'author_info'
                }
            },
            {
                '$unwind': '$author_info'
            },
            # Lookup para obtener nombres de tags
            {
                '$lookup': {
                    'from': 'tags',
                    'let': { 'tag_ids': '$tags' },
                    'pipeline': [
                        {
                            '$match': {
                                '$expr': {
                                    '$in': ['$_id', '$$tag_ids']
                                }
                            }
                        },
                        {
                            '$project': {
                                'tname': 1,
                                '_id': 0
                            }
                        }
                    ],
                    'as': 'tags_info'
                }
            },
            # Lookup para obtener nombres de categorías
            {
                '$lookup': {
                    'from': 'categories',
                    'let': { 'cat_ids': '$categories' },
                    'pipeline': [
                        {
                            '$match': {
                                '$expr': {
                                    '$in': ['$_id', '$$cat_ids']
                                }
                            }
                        },
                        {
                            '$project': {
                                'cname': 1,
                                '_id': 0
                            }
                        }
                    ],
                    'as': 'categories_info'
                }
            },
            {
                '$project': {
                    'articulo_id': '$_id',
                    'user_id': '$author_id',
                    'user_name': '$author_info.name',
                    'titulo': '$title',
                    'content': '$content',
                    'tags': '$tags_info',  # Nombres de tags
                    'categories': '$categories_info',  # Nombres de categorías
                    'created_at': 1
                }
            }
        ]
        
        cursor = mongo.db.articles.aggregate(pipeline)
        articulos_serializados = json.loads(json_util.dumps(cursor))
        return jsonify(articulos_serializados)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# POST /api/articulos
@articulos_bp.route('', methods=['POST'])
def create_articulo():
    data = request.get_json()
    try:
        # Encontrar el ID más alto actual
        last_article = mongo.db.articles.find_one(sort=[("_id", -1)])
        new_id = (last_article["_id"] + 1) if last_article else 1

        new_article = {
            "_id": new_id,
            "title": data.get('titulo'),
            "content": data.get('article_text'),
            "author_id": data.get('user_id'),
            "tags": data.get('tags', []),
            "categories": data.get('categories', []),
            "created_at": datetime.datetime.utcnow()
        }
        
        result = mongo.db.articles.insert_one(new_article)
        
        new_doc = mongo.db.articles.find_one({"_id": result.inserted_id})
        return jsonify(json.loads(json_util.dumps(new_doc))), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# DELETE /api/articulos/<id>
@articulos_bp.route('/<int:id>', methods=['DELETE'])
def delete_articulo(id):
    try:
        result = mongo.db.articles.delete_one({"_id": id})

        if result.deleted_count == 0:
            return jsonify({"error": "Artículo no encontrado"}), 404
            
        return "", 204
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# GET /api/articulos/<id>/comentarios - Nuevo endpoint para comentarios de un artículo
@articulos_bp.route('/<int:id>/comentarios', methods=['GET'])
def get_comentarios_articulo(id):
    try:
        # Pipeline para obtener comentarios de un artículo específico
        pipeline = [
            {
                '$match': {
                    'article_id': id
                }
            },
            {
                '$lookup': {
                    'from': 'users',
                    'localField': 'user_id',
                    'foreignField': '_id',
                    'as': 'user_info'
                }
            },
            {
                '$unwind': '$user_info'
            },
            {
                '$project': {
                    '_id': 1,
                    'comment': 1,
                    'created_at': 1,
                    'user_name': '$user_info.name',
                    'user_id': 1
                }
            },
            {
                '$sort': {'created_at': -1}  # Más recientes primero
            }
        ]
        
        comentarios = list(mongo.db.comments.aggregate(pipeline))
        
        return json.loads(json_util.dumps({
            "articulo_id": id,
            "count": len(comentarios),
            "comentarios": comentarios
        }))
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500