from flask import Blueprint, request, jsonify
from extensions import mongo
from bson import json_util
import json
import datetime # Para añadir la fecha de creación

comentarios_bp = Blueprint('comentarios', __name__)

# GET /api/comentarios
@comentarios_bp.route('', methods=['GET']) # <-- CORREGIDO: de '/' a ''
def get_comentarios():
    try:
        # --- LÓGICA CORREGIDA ---
        # 1. La colección es 'comments' (según tu insertMany de scriptbasemongo.txt)
        # 2. Implementamos $lookup para obtener datos de 'users' y 'articulos'
        pipeline = [
            {
                '$lookup': {
                    'from': 'users', # Colección de usuarios
                    'localField': 'user_id',
                    'foreignField': '_id',
                    'as': 'user_info'
                }
            },
            {
                '$lookup': {
                    'from': 'articles', # Colección de artículos
                    'localField': 'article_id',
                    'foreignField': '_id',
                    'as': 'article_info'
                }
            },
            # $unwind para convertir el array de $lookup en un objeto
            {
                '$unwind': '$user_info' 
            },
            {
                '$unwind': '$article_info'
            },
            # $project para seleccionar solo los campos que queremos
            {
                '$project': {
                    '_id': 1,
                    'comment': 1,
                    'created_at': 1,
                    'user_name': '$user_info.name', # Traemos el nombre de usuario
                    'article_title': '$article_info.title', # Traemos el título del artículo
                    'article_id': 1,  # Esto le dice a Mongo que mantenga el campo 'article_id' original
                    'user_id': 1
                }
            }
        ]
        
        cursor = mongo.db.comments.aggregate(pipeline)
        comentarios = json.loads(json_util.dumps(cursor))
        return jsonify(comentarios)
        
    except Exception as e:
        return jsonify(error=str(e)), 500

# POST /api/comentarios
@comentarios_bp.route('', methods=['POST']) # <-- CORREGIDO: de '/' a ''
def create_comentario():
    try:
        data = request.get_json()
        
        # --- LÓGICA CORREGIDA ---
        # Campos de la DB: article_id, user_id, comment
        if 'articulo_id' not in data or 'user_id' not in data or 'texto_com' not in data:
            return jsonify({"error": "Faltan los campos 'article_id', 'user_id' o 'texto_com'"}), 400
        print(data)
        new_comment = {
            "article_id": data.get('articulo_id'),
            "user_id": data.get('user_id'),
            "comment": data.get('texto_com'),
            "created_at": datetime.datetime.utcnow() # Añadir fecha de creación
        }
        
        # Usamos la colección 'comments'
        result = mongo.db.comments.insert_one(new_comment)
        
        new_doc = mongo.db.comments.find_one({"_id": result.inserted_id})
        return jsonify(json.loads(json_util.dumps(new_doc))), 201
        
    except Exception as e:
        return jsonify(error=str(e)), 500

# DELETE /api/comentarios/<id>
@comentarios_bp.route('/<int:id>', methods=['DELETE'])
def delete_comentario(id):
    try:
        # --- LÓGICA CORREGIDA ---
        # 1. Usamos la colección 'comments'
        # 2. El ID en tu script es '_id' (y es un Int)
        result = mongo.db.comments.delete_one({"_id": id})
        
        if result.deleted_count == 0:
            return jsonify({"error": "Comentario no encontrado"}), 404
            
        return "", 204 # Éxito sin contenido
        
    except Exception as e:
        return jsonify(error=str(e)), 500