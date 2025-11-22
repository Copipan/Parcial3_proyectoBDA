from flask import Blueprint, request, jsonify
from extensions import mongo
import urllib.parse
from bson import json_util
import json

tags_bp = Blueprint('tags', __name__)

# GET /api/tags
@tags_bp.route('', methods=['GET']) # <-- CORREGIDO: de '/' a ''
def get_tags():
    try:
        # --- LÓGICA CORREGIDA ---
        cursor = mongo.db.tags.find()
        tags = json.loads(json_util.dumps(cursor))
        return jsonify(tags)
    except Exception as e:
        return jsonify(error=str(e)), 500

# POST /api/tags
@tags_bp.route('', methods=['POST']) # <-- CORREGIDO: de '/' a ''
def create_tag():
    try:
        data = request.get_json() # Espera: { tname, tagurl }
        
        # --- LÓGICA CORREGIDA ---
        # Validar campos correctos (de scriptbasemongo.txt)
        if 'tname' not in data or 'tagurl' not in data:
            return jsonify({"error": "Faltan los campos 'tname' y 'tagurl'"}), 400
        
        # Verificar duplicados
        if mongo.db.tags.find_one({"tname": data['tname']}):
            return jsonify({"error": "Ese 'tname' de tag ya existe"}), 409

        result = mongo.db.tags.insert_one(data)
        
        new_tag = mongo.db.tags.find_one({"_id": result.inserted_id})
        return jsonify(json.loads(json_util.dumps(new_tag))), 201
        
    except Exception as e:
        return jsonify(error=str(e)), 500

# PUT /api/tags/<tname> (Usamos 'tname' para consistencia)
@tags_bp.route('/<string:tname>', methods=['PUT'])
def update_tag(tname):
    try:
        data = request.get_json() # Espera: { tname, tagurl }
        decoded_name = urllib.parse.unquote(tname)
        
        # Validar campos
        if 'tname' not in data or 'tagurl' not in data:
            return jsonify({"error": "Faltan los campos 'tname' y 'tagurl'"}), 400

        # --- LÓGICA CORREGIDA ---
        # Busca por 'tname' (de scriptbasemongo.txt)
        result = mongo.db.tags.update_one(
            {"tname": decoded_name},
            {"$set": data}
        )
        
        if result.matched_count == 0:
            return jsonify({"error": "Tag no encontrado"}), 404
            
        return jsonify({"message": "Tag actualizado"})
        
    except Exception as e:
        return jsonify(error=str(e)), 500

# DELETE /api/tags/<tname>
@tags_bp.route('/<string:tname>', methods=['DELETE'])
def delete_tag(tname):
    try:
        decoded_name = urllib.parse.unquote(tname)
        
        # --- LÓGICA CORREGIDA ---
        # Busca por 'tname' (de scriptbasemongo.txt)
        result = mongo.db.tags.delete_one({"tname": decoded_name})
        
        if result.deleted_count == 0:
            return jsonify({"error": "Tag no encontrado"}), 404
            
        return "", 204 # Éxito sin contenido
        
    except Exception as e:
        return jsonify(error=str(e)), 500