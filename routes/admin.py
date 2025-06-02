from flask import Blueprint, request, jsonify, render_template
from models.database import db
import logging

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Mapeo de tipos de producto a tablas
TABLE_MAPPING = {
    'personal': 'kok_personal',
    'molde_rect': 'kok_molde_rect', 
    'molde_circular': 'kok_molde_circular',
    'promo': 'kok_promo'
}

@admin_bp.route('/manage', methods=['GET'])
def manage_products_page():
    """Página de administración de productos"""
    return render_template('manage.html')

@admin_bp.route('/products/<product_type>', methods=['GET'])
def get_products_by_type(product_type):
    """Obtener todos los productos de un tipo específico"""
    try:
        if product_type not in TABLE_MAPPING:
            return jsonify({'error': 'Tipo de producto inválido'}), 400
        
        table_name = TABLE_MAPPING[product_type]
        
        # Obtener parámetros de consulta
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        search = request.args.get('search', '')
        disponible_filter = request.args.get('disponible')
        
        # Construir WHERE clause
        where_conditions = []
        params = []
        
        if search:
            where_conditions.append("(nombre LIKE %s OR descripcion LIKE %s OR categoria LIKE %s)")
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])
        
        if disponible_filter is not None and disponible_filter != '':
            where_conditions.append("disponible = %s")
            params.append(disponible_filter == 'true')
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # Contar total de productos
        count_query = f"SELECT COUNT(*) as total FROM {table_name} {where_clause}"
        total_count = db.execute_query(count_query, params)[0]['total']
        
        # Obtener productos paginados
        offset = (page - 1) * per_page
        products_query = f"""
            SELECT * FROM {table_name} {where_clause} 
            ORDER BY created_at DESC 
            LIMIT %s OFFSET %s
        """
        params.extend([per_page, offset])
        
        products = db.execute_query(products_query, params)
        
        # Procesar imágenes para frontend
        for product in products:
            if product['imagen']:
                product['imagen_list'] = product['imagen'].split(',')
            else:
                product['imagen_list'] = []
        
        total_pages = (total_count + per_page - 1) // per_page
        
        return jsonify({
            'success': True,
            'products': products,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_count': total_count,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            },
            'product_type': product_type
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo productos de {product_type}: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@admin_bp.route('/product/<product_type>/<int:product_id>', methods=['GET'])
def get_product_detail(product_type, product_id):
    """Obtener detalles de un producto específico"""
    try:
        if product_type not in TABLE_MAPPING:
            return jsonify({'error': 'Tipo de producto inválido'}), 400
        
        table_name = TABLE_MAPPING[product_type]
        
        product = db.execute_query(
            f"SELECT * FROM {table_name} WHERE id = %s",
            (product_id,)
        )
        
        if not product:
            return jsonify({'error': 'Producto no encontrado'}), 404
        
        product = product[0]
        
        # Procesar imágenes
        if product['imagen']:
            product['imagen_list'] = product['imagen'].split(',')
        else:
            product['imagen_list'] = []
        
        return jsonify({
            'success': True,
            'product': product,
            'product_type': product_type
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo producto {product_id}: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@admin_bp.route('/stats', methods=['GET'])
def get_statistics():
    """Obtener estadísticas de productos"""
    try:
        stats = {}
        
        for product_type, table_name in TABLE_MAPPING.items():
            # Contar productos por estado
            total_query = f"SELECT COUNT(*) as total FROM {table_name}"
            available_query = f"SELECT COUNT(*) as available FROM {table_name} WHERE disponible = TRUE"
            unavailable_query = f"SELECT COUNT(*) as unavailable FROM {table_name} WHERE disponible = FALSE"
            
            total = db.execute_query(total_query)[0]['total']
            available = db.execute_query(available_query)[0]['available']
            unavailable = db.execute_query(unavailable_query)[0]['unavailable']
            
            stats[product_type] = {
                'total': total,
                'available': available,
                'unavailable': unavailable,
                'table_name': table_name
            }
        
        # Estadísticas generales
        total_products = sum(stat['total'] for stat in stats.values())
        total_available = sum(stat['available'] for stat in stats.values())
        total_unavailable = sum(stat['unavailable'] for stat in stats.values())
        
        return jsonify({
            'success': True,
            'stats_by_type': stats,
            'general_stats': {
                'total_products': total_products,
                'total_available': total_available,
                'total_unavailable': total_unavailable
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estadísticas: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@admin_bp.route('/search', methods=['GET'])
def search_products():
    """Buscar productos en todas las tablas"""
    try:
        search_term = request.args.get('q', '').strip()
        if not search_term:
            return jsonify({'error': 'Término de búsqueda requerido'}), 400
        
        results = {}
        search_pattern = f"%{search_term}%"
        
        for product_type, table_name in TABLE_MAPPING.items():
            query = f"""
                SELECT *, '{product_type}' as product_type FROM {table_name} 
                WHERE nombre LIKE %s OR descripcion LIKE %s OR categoria LIKE %s
                ORDER BY created_at DESC
                LIMIT 10
            """
            
            products = db.execute_query(query, [search_pattern, search_pattern, search_pattern])
            
            # Procesar imágenes
            for product in products:
                if product['imagen']:
                    product['imagen_list'] = product['imagen'].split(',')
                else:
                    product['imagen_list'] = []
            
            results[product_type] = products
        
        # Contar total de resultados
        total_results = sum(len(products) for products in results.values())
        
        return jsonify({
            'success': True,
            'search_term': search_term,
            'results': results,
            'total_results': total_results
        })
        
    except Exception as e:
        logger.error(f"❌ Error en búsqueda: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@admin_bp.route('/bulk-toggle', methods=['POST'])
def bulk_toggle_availability():
    """Cambiar disponibilidad de múltiples productos"""
    try:
        data = request.get_json()
        product_type = data.get('product_type')
        product_ids = data.get('product_ids', [])
        new_status = data.get('available', True)
        
        if not product_type or product_type not in TABLE_MAPPING:
            return jsonify({'error': 'Tipo de producto inválido'}), 400
        
        if not product_ids:
            return jsonify({'error': 'IDs de productos requeridos'}), 400
        
        table_name = TABLE_MAPPING[product_type]
        
        # Construir query para múltiples IDs
        placeholders = ','.join(['%s'] * len(product_ids))
        query = f"UPDATE {table_name} SET disponible = %s WHERE id IN ({placeholders})"
        params = [new_status] + product_ids
        
        db.execute_query(query, params)
        
        logger.info(f"✅ Disponibilidad actualizada para {len(product_ids)} productos en {table_name}")
        
        return jsonify({
            'success': True,
            'message': f'{len(product_ids)} productos {"activados" if new_status else "desactivados"}',
            'updated_count': len(product_ids)
        })
        
    except Exception as e:
        logger.error(f"❌ Error en actualización masiva: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@admin_bp.route('/products/all', methods=['GET'])
def get_all_products():
    """Obtener todos los productos de todas las categorías"""
    try:
        # Obtener parámetros de consulta
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        search = request.args.get('search', '')
        disponible_filter = request.args.get('disponible')
        
        all_products = []
        
        # Recorrer todas las tablas
        for product_type, table_name in TABLE_MAPPING.items():
            # Construir WHERE clause
            where_conditions = []
            params = []
            
            if search:
                where_conditions.append("(nombre LIKE %s OR descripcion LIKE %s OR categoria LIKE %s)")
                search_term = f"%{search}%"
                params.extend([search_term, search_term, search_term])
            
            if disponible_filter is not None and disponible_filter != '':
                where_conditions.append("disponible = %s")
                params.append(disponible_filter == 'true')
            
            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            
            # Obtener productos de esta tabla
            products_query = f"""
                SELECT *, '{product_type}' as product_type FROM {table_name} {where_clause}
                ORDER BY created_at DESC
            """
            
            products = db.execute_query(products_query, params)
            
            # Procesar imágenes para cada producto
            for product in products:
                if product['imagen']:
                    product['imagen_list'] = product['imagen'].split(',')
                else:
                    product['imagen_list'] = []
            
            all_products.extend(products)
        
        # Ordenar todos los productos por fecha de creación
        all_products.sort(key=lambda x: x['created_at'], reverse=True)
        
        # Aplicar paginación
        total_count = len(all_products)
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        paginated_products = all_products[start_index:end_index]
        
        total_pages = (total_count + per_page - 1) // per_page
        
        return jsonify({
            'success': True,
            'products': paginated_products,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_count': total_count,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            },
            'product_type': 'all'
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo todos los productos: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500 