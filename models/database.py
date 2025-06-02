import pymysql
from config import Config
import logging
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        """Establecer conexión con MySQL"""
        try:
            self.connection = pymysql.connect(
                host=Config.DB_HOST,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                port=Config.DB_PORT,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False,
                # Configuraciones para evitar timeouts
                connect_timeout=30,
                read_timeout=30,
                write_timeout=30
            )
            logger.info("✅ Conexión exitosa a MySQL")
            self.create_tables()
        except Exception as e:
            logger.error(f"❌ Error conectando a MySQL: {e}")
            raise e
    
    def ensure_connection(self):
        """
        Verificar y restablecer conexión si es necesario
        """
        try:
            if self.connection is None:
                logger.warning("⚠️ Conexión es None, reconectando...")
                self.connect()
                return
            
            # Probar la conexión con un ping
            self.connection.ping(reconnect=True)
            
        except Exception as e:
            logger.warning(f"⚠️ Conexión perdida, reconectando: {e}")
            try:
                self.connect()
            except Exception as reconnect_error:
                logger.error(f"❌ Error reconectando: {reconnect_error}")
                raise reconnect_error
    
    def get_fresh_connection(self):
        """
        Obtener una nueva conexión fresca para operaciones críticas
        """
        try:
            return pymysql.connect(
                host=Config.DB_HOST,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                port=Config.DB_PORT,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False,
                connect_timeout=30,
                read_timeout=30,
                write_timeout=30
            )
        except Exception as e:
            logger.error(f"❌ Error creando nueva conexión: {e}")
            raise e
    
    def create_tables(self):
        """Crear todas las tablas si no existen"""
        tables = {
            'kok_personal': """
                CREATE TABLE IF NOT EXISTS kok_personal (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nombre VARCHAR(255) NOT NULL,
                    descripcion TEXT NOT NULL,
                    sabor VARCHAR(255) NOT NULL,
                    categoria VARCHAR(255) NOT NULL,
                    imagen TEXT NOT NULL,
                    precio DECIMAL(10,2) NOT NULL,
                    disponible BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            'kok_molde_rect': """
                CREATE TABLE IF NOT EXISTS kok_molde_rect (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nombre VARCHAR(255) NOT NULL,
                    descripcion TEXT NOT NULL,
                    sabor VARCHAR(255) NOT NULL,
                    porciones INT NOT NULL,
                    categoria VARCHAR(255) NOT NULL,
                    imagen TEXT NOT NULL,
                    precio DECIMAL(10,2) NOT NULL,
                    disponible BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            'kok_molde_circular': """
                CREATE TABLE IF NOT EXISTS kok_molde_circular (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nombre VARCHAR(255) NOT NULL,
                    descripcion TEXT NOT NULL,
                    sabor VARCHAR(255) NOT NULL,
                    porciones INT NOT NULL,
                    categoria VARCHAR(255) NOT NULL,
                    tamaño_molde DECIMAL(5,2) NOT NULL,
                    imagen TEXT NOT NULL,
                    precio DECIMAL(10,2) NOT NULL,
                    disponible BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            'kok_promo': """
                CREATE TABLE IF NOT EXISTS kok_promo (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nombre VARCHAR(255) NOT NULL,
                    descripcion TEXT NOT NULL,
                    categoria VARCHAR(255) NOT NULL,
                    imagen TEXT NOT NULL,
                    precio DECIMAL(10,2) NOT NULL,
                    disponible BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            'kok_accesorios': """
                CREATE TABLE IF NOT EXISTS kok_accesorios (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nombre VARCHAR(255) NOT NULL,
                    descripcion TEXT NOT NULL,
                    precio DECIMAL(10,2) NOT NULL,
                    imagen TEXT NOT NULL,
                    disponible BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
        }
        
        try:
            with self.connection.cursor() as cursor:
                for table_name, sql in tables.items():
                    cursor.execute(sql)
                    logger.info(f"✅ Tabla {table_name} verificada/creada")
                self.connection.commit()
                self.verify_columns()
        except Exception as e:
            logger.error(f"❌ Error creando tablas: {e}")
            raise e
    
    def verify_columns(self):
        """Verificar que todas las columnas existan, agregar 'disponible' si falta"""
        tables_to_check = ['kok_personal', 'kok_molde_rect', 'kok_molde_circular', 'kok_promo', 'kok_accesorios']
        
        try:
            with self.connection.cursor() as cursor:
                for table in tables_to_check:
                    # Verificar si existe columna 'disponible'
                    cursor.execute(f"SHOW COLUMNS FROM {table} LIKE 'disponible'")
                    if not cursor.fetchone():
                        cursor.execute(f"ALTER TABLE {table} ADD COLUMN disponible BOOLEAN DEFAULT TRUE")
                        logger.info(f"✅ Columna 'disponible' agregada a {table}")
                self.connection.commit()
        except Exception as e:
            logger.error(f"❌ Error verificando columnas: {e}")
    
    def execute_query(self, query: str, params: Optional[tuple] = None, use_fresh_connection: bool = False) -> Any:
        """
        Ejecutar query con parámetros con manejo robusto de conexiones
        
        Args:
            query: SQL query a ejecutar
            params: Parámetros para la query
            use_fresh_connection: Si usar una conexión fresca (para operaciones críticas)
        
        Returns:
            Resultado de la query
        """
        connection_to_use = None
        should_close_connection = False
        
        try:
            if use_fresh_connection:
                connection_to_use = self.get_fresh_connection()
                should_close_connection = True
                logger.debug("🔄 Usando conexión fresca")
            else:
                self.ensure_connection()
                connection_to_use = self.connection
            
            with connection_to_use.cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                # Determinar tipo de query
                query_type = query.strip().upper()
                
                if query_type.startswith('SELECT'):
                    result = cursor.fetchall()
                    logger.debug(f"🔍 SELECT ejecutado: {len(result)} filas")
                    return result
                else:
                    connection_to_use.commit()
                    result = cursor.lastrowid
                    logger.debug(f"✅ {query_type.split()[0]} ejecutado: lastrowid={result}")
                    return result
                    
        except Exception as e:
            logger.error(f"❌ Error ejecutando query: {e}")
            logger.error(f"   Query: {query[:100]}...")
            logger.error(f"   Params: {params}")
            
            # Intentar con conexión fresca si no se estaba usando ya
            if not use_fresh_connection:
                logger.warning("🔄 Reintentando con conexión fresca...")
                try:
                    return self.execute_query(query, params, use_fresh_connection=True)
                except Exception as retry_error:
                    logger.error(f"❌ Error en reintento: {retry_error}")
                    raise retry_error
            else:
                raise e
                
        finally:
            if should_close_connection and connection_to_use:
                try:
                    connection_to_use.close()
                    logger.debug("🔒 Conexión fresca cerrada")
                except:
                    pass
    
    def close(self):
        """Cerrar conexión"""
        if self.connection:
            try:
                self.connection.close()
                logger.info("🔒 Conexión MySQL cerrada")
            except:
                pass
            finally:
                self.connection = None

# Función para obtener una instancia de base de datos
def get_db_instance():
    """
    Obtener instancia de base de datos
    """
    return Database()

# Instancia global de la base de datos
db = get_db_instance() 