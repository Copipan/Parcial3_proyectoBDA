from flask import Blueprint, request, jsonify
from extensions import mongo
import urllib.parse
from bson import json_util
import json

categorias_bp = Blueprint('categorias', __name__)

# GET /api/categorias
@categorias_bp.route('', methods=['GET'])
def get_categorias():
    try:
        cursor = mongo.db.categories.find()
        categorias_list = list(cursor)
        
        # TRANSFORMAR LOS DATOS para que coincidan con el frontend
        categorias_transformadas = []
        for cat in categorias_list:
            categorias_transformadas.append({
                '_id': cat['_id'],
                'category_name': cat['cname'],  # Mapear cname → category_name
                'url_cat': f"/categoria/{cat['cname'].lower().replace(' ', '-')}"  # Generar URL automáticamente
            })
        
        categorias = json.loads(json_util.dumps(categorias_transformadas))
        return jsonify(categorias)
    except Exception as e:
        return jsonify(error=str(e)), 500

# POST /api/categorias
@categorias_bp.route('', methods=['POST'])
def create_categoria():
    try:
        data = request.get_json()
        
        # Validar campos (ahora sabemos que la DB usa 'cname')
        if 'category_name' not in data:
            return jsonify({"error": "Falta el campo 'category_name'"}), 400
        
        # Verificar duplicados por 'cname' (campo real en la DB)
        if mongo.db.categories.find_one({"cname": data['category_name']}):
            return jsonify({"error": "Ese nombre de categoría ya existe"}), 409

        # Crear documento con la estructura correcta para la DB
        new_doc = {
            "cname": data['category_name']  # Usar 'cname' que es el campo real
        }

        result = mongo.db.categories.insert_one(new_doc)
        
        # Devolver datos transformados para el frontend
        new_cat = mongo.db.categories.find_one({"_id": result.inserted_id})
        cat_transformada = {
            '_id': new_cat['_id'],
            'category_name': new_cat['cname'],
            'url_cat': f"/categoria/{new_cat['cname'].lower().replace(' ', '-')}"
        }
        return jsonify(json.loads(json_util.dumps(cat_transformada))), 201
        
    except Exception as e:
        return jsonify(error=str(e)), 500

# PUT /api/categorias/<originalName>
@categorias_bp.route('/<string:originalName>', methods=['PUT'])
def update_categoria(originalName):
    try:
        data = request.get_json()
        decoded_name = urllib.parse.unquote(originalName)
        
        # Validar campos
        if 'category_name' not in data:
            return jsonify({"error": "Falta el campo 'category_name'"}), 400

        # Actualizar usando 'cname' (campo real en la DB)
        result = mongo.db.categories.update_one(
            {"cname": decoded_name},  # Buscar por cname
            {"$set": {
                "cname": data.get('category_name')  # Actualizar cname
            }}
        )
        
        if result.matched_count == 0:
            return jsonify({"error": "Categoría no encontrada"}), 404
            
        return jsonify({"message": "Categoría actualizada"})
        
    except Exception as e:
        return jsonify(error=str(e)), 500

# DELETE /api/categorias/<name>
@categorias_bp.route('/<string:name>', methods=['DELETE'])
def delete_categoria(name):
    try:
        decoded_name = urllib.parse.unquote(name)
        
        # Buscar y eliminar por 'cname' (campo real en la DB)
        result = mongo.db.categories.delete_one({"cname": decoded_name})
        
        if result.deleted_count == 0:
            return jsonify({"error": "Categoría no encontrada"}), 404
            
        return "", 204
        
    except Exception as e:
        return jsonify(error=str(e)), 500