from flask import Blueprint, request, jsonify, render_template
from models.database import db
from utils.s3_handler import s3_handler
from utils.image_processor import image_processor
import logging

logger = logging.getLogger(__name__)

products_bp = Blueprint('products', __name__, url_prefix='/products')

# Mapeo de tipos de producto a tablas
TABLE_MAPPING = {
    'personal': 'kok_personal',
    'molde_rect': 'kok_molde_rect', 
    'molde_circular': 'kok_molde_circular',
    'promo': 'kok_promo'
}

@products_bp.route('/add', methods=['GET'])
def add_product_page():
    """Página para agregar productos"""
    return render_template('add_product.html')

@products_bp.route('/add', methods=['POST'])
def add_product():
    """Agregar nuevo producto según tipo de tabla"""
    try:
        # Obtener tipo de producto
        product_type = request.form.get('product_type')
        if not product_type or product_type not in TABLE_MAPPING:
            return jsonify({'error': 'Tipo de producto inválido'}), 400
        
        table_name = TABLE_MAPPING[product_type]
        
        # Validar imágenes
        files = request.files.getlist('images')
        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': 'Se requiere al menos una imagen'}), 400
        
        # Procesar y validar imágenes
        valid_files, errors = image_processor.validate_image_files(files)
        if errors:
            return jsonify({'error': f'Errores en imágenes: {", ".join(errors)}'}), 400
        
        # Redimensionar imágenes
        processed_files = image_processor.process_multiple_images(valid_files)
        
        # Subir imágenes a S3
        image_urls = s3_handler.upload_multiple_files(processed_files)
        if not image_urls:
            return jsonify({'error': 'Error subiendo imágenes'}), 500
        
        # Preparar datos según tipo de producto
        product_data = _prepare_product_data(product_type, request.form, image_urls)
        
        # Insertar en base de datos
        query, values = _build_insert_query(table_name, product_data)
        product_id = db.execute_query(query, values)
        
        logger.info(f"✅ Producto creado en {table_name}: ID {product_id}")
        return jsonify({
            'success': True, 
            'message': 'Producto agregado exitosamente',
            'product_id': product_id
        })
        
    except Exception as e:
        logger.error(f"❌ Error agregando producto: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@products_bp.route('/edit/<product_type>/<int:product_id>', methods=['PUT'])
def edit_product(product_type, product_id):
    """Editar producto existente"""
    try:
        if product_type not in TABLE_MAPPING:
            return jsonify({'error': 'Tipo de producto inválido'}), 400
        
        table_name = TABLE_MAPPING[product_type]
        
        # Obtener producto actual
        current_product = db.execute_query(
            f"SELECT * FROM {table_name} WHERE id = %s", 
            (product_id,)
        )
        if not current_product:
            return jsonify({'error': 'Producto no encontrado'}), 404
        
        current_product = current_product[0]
        
        # Procesar nuevas imágenes si las hay
        image_urls = current_product['imagen']
        files = request.files.getlist('images')
        
        if files and any(f.filename != '' for f in files):
            # Eliminar imágenes anteriores de S3
            s3_handler.delete_multiple_files(current_product['imagen'])
            
            # Procesar nuevas imágenes
            valid_files, errors = image_processor.validate_image_files(files)
            if errors:
                return jsonify({'error': f'Errores en imágenes: {", ".join(errors)}'}), 400
            
            processed_files = image_processor.process_multiple_images(valid_files)
            image_urls = s3_handler.upload_multiple_files(processed_files)
        
        # Preparar datos actualizados
        product_data = _prepare_product_data(product_type, request.form, image_urls)
        
        # Actualizar en base de datos
        query, values = _build_update_query(table_name, product_data, product_id)
        db.execute_query(query, values)
        
        logger.info(f"✅ Producto editado en {table_name}: ID {product_id}")
        return jsonify({
            'success': True,
            'message': 'Producto editado exitosamente'
        })
        
    except Exception as e:
        logger.error(f"❌ Error editando producto: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@products_bp.route('/delete/<product_type>/<int:product_id>', methods=['DELETE'])
def delete_product(product_type, product_id):
    """Eliminar producto"""
    try:
        if product_type not in TABLE_MAPPING:
            return jsonify({'error': 'Tipo de producto inválido'}), 400
        
        table_name = TABLE_MAPPING[product_type]
        
        # Obtener producto para eliminar imágenes
        product = db.execute_query(
            f"SELECT imagen FROM {table_name} WHERE id = %s", 
            (product_id,)
        )
        if not product:
            return jsonify({'error': 'Producto no encontrado'}), 404
        
        # Eliminar imágenes de S3
        s3_handler.delete_multiple_files(product[0]['imagen'])
        
        # Eliminar de base de datos
        db.execute_query(f"DELETE FROM {table_name} WHERE id = %s", (product_id,))
        
        logger.info(f"✅ Producto eliminado de {table_name}: ID {product_id}")
        return jsonify({
            'success': True,
            'message': 'Producto eliminado exitosamente'
        })
        
    except Exception as e:
        logger.error(f"❌ Error eliminando producto: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@products_bp.route('/toggle/<product_type>/<int:product_id>', methods=['POST'])
def toggle_availability(product_type, product_id):
    """Toggle disponibilidad de producto"""
    try:
        if product_type not in TABLE_MAPPING:
            return jsonify({'error': 'Tipo de producto inválido'}), 400
        
        table_name = TABLE_MAPPING[product_type]
        
        # Obtener estado actual
        current = db.execute_query(
            f"SELECT disponible FROM {table_name} WHERE id = %s", 
            (product_id,)
        )
        if not current:
            return jsonify({'error': 'Producto no encontrado'}), 404
        
        # Toggle estado
        new_status = not current[0]['disponible']
        db.execute_query(
            f"UPDATE {table_name} SET disponible = %s WHERE id = %s",
            (new_status, product_id)
        )
        
        logger.info(f"✅ Disponibilidad cambiada en {table_name}: ID {product_id} -> {new_status}")
        return jsonify({
            'success': True,
            'disponible': new_status,
            'message': f'Producto {"activado" if new_status else "desactivado"}'
        })
        
    except Exception as e:
        logger.error(f"❌ Error cambiando disponibilidad: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

def _prepare_product_data(product_type, form_data, image_urls):
    """Preparar datos según tipo de producto"""
    base_data = {
        'nombre': form_data.get('nombre'),
        'descripcion': form_data.get('descripcion'),
        'categoria': form_data.get('categoria'),
        'imagen': image_urls,
        'precio': float(form_data.get('precio', 0))
    }
    
    if product_type in ['personal', 'molde_rect', 'molde_circular']:
        base_data['sabor'] = form_data.get('sabor')
    
    if product_type in ['molde_rect', 'molde_circular']:
        base_data['porciones'] = int(form_data.get('porciones', 0))
    
    if product_type == 'molde_circular':
        base_data['tamaño_molde'] = float(form_data.get('tamaño_molde', 0))
    
    return base_data

def _build_insert_query(table_name, data):
    """Construir query INSERT"""
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['%s'] * len(data))
    query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
    return query, list(data.values())

def _build_update_query(table_name, data, product_id):
    """Construir query UPDATE"""
    set_clause = ', '.join([f"{key} = %s" for key in data.keys()])
    query = f"UPDATE {table_name} SET {set_clause} WHERE id = %s"
    values = list(data.values()) + [product_id]
    return query, values 