import boto3
from botocore.exceptions import ClientError
from config import Config
import logging
import uuid
import os
from datetime import datetime
import pathlib
import re
from typing import Tuple, Optional, List

logger = logging.getLogger(__name__)

class S3Handler:
    """
    Manejador de archivos AWS S3 para Kokorito
    Sin uso de ACLs - acceso público configurado por política del bucket
    """
    
    def __init__(self):
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
                region_name=Config.AWS_DEFAULT_REGION
            )
            self.bucket_name = Config.S3_BUCKET
            self.region = Config.AWS_DEFAULT_REGION
            
            if not self.bucket_name:
                raise ValueError("S3_BUCKET no configurado")
                
            logger.info(f"✅ S3Handler inicializado - Bucket: {self.bucket_name}")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando S3Handler: {e}")
            raise
    
    def upload_file(self, file_obj, filename: str) -> str:
        """
        Subir archivo individual a S3
        
        Args:
            file_obj: Objeto file de Flask
            filename: Nombre original del archivo
            
        Returns:
            str: URL pública del archivo en S3
        """
        try:
            # Generar nombre único con estructura de carpetas
            unique_filename = self._generate_unique_filename(filename)
            s3_key = f"productos/{unique_filename}"
            
            # Subir archivo sin ACL (acceso público por política del bucket)
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': self._get_content_type(filename),
                    'CacheControl': 'max-age=31536000',  # Cache por 1 año
                    'ContentDisposition': 'inline'
                }
            )
            
            # Generar URL pública
            url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
            logger.info(f"✅ Archivo subido exitosamente: {unique_filename}")
            return url
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"❌ Error AWS subiendo archivo: {error_code} - {error_message}")
            raise Exception(f"Error subiendo archivo: {error_message}")
        except Exception as e:
            logger.error(f"❌ Error general subiendo archivo: {e}")
            raise Exception(f"Error subiendo archivo: {str(e)}")
    
    def upload_multiple_files(self, files: List) -> str:
        """
        Subir múltiples archivos y retornar URLs separadas por coma
        
        Args:
            files: Lista de objetos file
            
        Returns:
            str: URLs separadas por coma
        """
        urls = []
        
        for file in files:
            if file and hasattr(file, 'filename') and file.filename != '':
                try:
                    url = self.upload_file(file, file.filename)
                    urls.append(url)
                except Exception as e:
                    logger.error(f"❌ Error subiendo archivo {file.filename}: {e}")
                    # Si ya se subieron algunos archivos, limpiarlos
                    if urls:
                        self.delete_multiple_files(','.join(urls))
                    raise e
        
        result = ','.join(urls) if urls else ''
        logger.info(f"✅ {len(urls)} archivos subidos exitosamente")
        return result
    
    def delete_file(self, file_url: str) -> bool:
        """
        Eliminar archivo de S3 usando la URL
        
        Args:
            file_url: URL completa del archivo
            
        Returns:
            bool: True si se eliminó exitosamente
        """
        try:
            # Extraer S3 key de la URL
            s3_key = self._extract_s3_key_from_url(file_url)
            if not s3_key:
                logger.warning(f"⚠️ No se pudo extraer S3 key de URL: {file_url}")
                return False
            
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            logger.info(f"✅ Archivo eliminado: {s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"❌ Error AWS eliminando archivo: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error eliminando archivo: {e}")
            return False
    
    def delete_multiple_files(self, urls_string: str) -> int:
        """
        Eliminar múltiples archivos usando string de URLs separadas por coma
        
        Args:
            urls_string: URLs separadas por coma
            
        Returns:
            int: Número de archivos eliminados exitosamente
        """
        if not urls_string or urls_string.strip() == '':
            return 0
        
        urls = [url.strip() for url in urls_string.split(',') if url.strip()]
        deleted_count = 0
        
        for url in urls:
            if self.delete_file(url):
                deleted_count += 1
        
        logger.info(f"✅ {deleted_count}/{len(urls)} archivos eliminados")
        return deleted_count
    
    def _generate_unique_filename(self, original_filename: str) -> str:
        """
        Generar nombre único para el archivo manteniendo la extensión
        
        Args:
            original_filename: Nombre original del archivo
            
        Returns:
            str: Nombre único sanitizado
        """
        # Extraer extensión y nombre base
        file_path = pathlib.Path(original_filename)
        file_ext = file_path.suffix.lower()
        base_name = file_path.stem
        
        # Sanitizar nombre base
        clean_name = re.sub(r'[^\w\-_.]', '_', base_name)
        clean_name = re.sub(r'_+', '_', clean_name)[:20]  # Limitar longitud
        
        # Generar componentes únicos
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        
        return f"{clean_name}_{timestamp}_{unique_id}{file_ext}"
    
    def _extract_s3_key_from_url(self, url: str) -> Optional[str]:
        """
        Extraer S3 key de una URL completa
        
        Args:
            url: URL completa del archivo
            
        Returns:
            Optional[str]: S3 key o None si no se puede extraer
        """
        try:
            # URL formato: https://bucket.s3.region.amazonaws.com/path/to/file
            if self.bucket_name in url and "amazonaws.com" in url:
                return url.split('amazonaws.com/')[-1]
            return None
        except Exception:
            return None
    
    def _get_content_type(self, filename: str) -> str:
        """
        Obtener content type basado en la extensión del archivo
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            str: Content type MIME
        """
        import mimetypes
        
        content_type, _ = mimetypes.guess_type(filename)
        if content_type:
            return content_type
        
        # Fallback para extensiones comunes
        file_ext = pathlib.Path(filename).suffix.lower()
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg', 
            '.png': 'image/png',
            '.webp': 'image/webp',
            '.gif': 'image/gif'
        }
        
        return content_types.get(file_ext, 'application/octet-stream')
    
    def validate_file_for_upload(self, file, max_size: int = 10 * 1024 * 1024) -> Tuple[bool, Optional[str]]:
        """
        Validar archivo antes de subirlo
        
        Args:
            file: Objeto file
            max_size: Tamaño máximo en bytes (default 10MB)
            
        Returns:
            Tuple[bool, Optional[str]]: (es_válido, mensaje_error)
        """
        try:
            # Verificar que existe y tiene nombre
            if not file or not hasattr(file, 'filename') or file.filename == '':
                return False, "No se proporcionó archivo"
            
            # Verificar extensión
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp']
            file_ext = pathlib.Path(file.filename).suffix.lower()
            
            if file_ext not in allowed_extensions:
                return False, f"Extensión no permitida. Permitidas: {', '.join(allowed_extensions)}"
            
            # Verificar tamaño
            file.seek(0, 2)  # Ir al final del archivo
            file_size = file.tell()
            file.seek(0)  # Volver al inicio
            
            if file_size > max_size:
                max_mb = max_size / (1024 * 1024)
                return False, f"Archivo muy grande. Máximo: {max_mb:.1f}MB"
            
            if file_size == 0:
                return False, "El archivo está vacío"
            
            return True, None
            
        except Exception as e:
            return False, f"Error validando archivo: {str(e)}"

# Instancia global del handler S3
s3_handler = S3Handler() 