from PIL import Image
import io
from config import Config
import logging

logger = logging.getLogger(__name__)

class ImageProcessor:
    def __init__(self):
        self.max_width = Config.MAX_IMAGE_WIDTH
        self.allowed_extensions = Config.ALLOWED_EXTENSIONS
    
    def is_allowed_file(self, filename):
        """
        Verificar si el archivo tiene una extensión permitida
        """
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def resize_image(self, image_file):
        """
        Redimensionar imagen manteniendo proporción si excede el ancho máximo
        """
        try:
            # Abrir imagen
            image = Image.open(image_file)
            
            # Convertir a RGB si es necesario (para JPEG)
            if image.mode in ('RGBA', 'LA', 'P'):
                # Crear fondo blanco para imágenes con transparencia
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Obtener dimensiones originales
            original_width, original_height = image.size
            
            # Verificar si necesita redimensionamiento
            if original_width > self.max_width:
                # Calcular nueva altura manteniendo proporción
                ratio = self.max_width / original_width
                new_height = int(original_height * ratio)
                
                # Redimensionar
                image = image.resize((self.max_width, new_height), Image.Resampling.LANCZOS)
                logger.info(f"✅ Imagen redimensionada: {original_width}x{original_height} → {self.max_width}x{new_height}")
            else:
                logger.info(f"✅ Imagen no necesita redimensionamiento: {original_width}x{original_height}")
            
            # Convertir a bytes
            output = io.BytesIO()
            
            # Determinar formato de salida basado en calidad/tamaño
            if original_width > 800 or original_height > 800:
                # Para imágenes grandes, usar JPEG con buena calidad
                image.save(output, format='JPEG', quality=85, optimize=True)
                output.content_type = 'image/jpeg'
            else:
                # Para imágenes pequeñas, mantener PNG si era PNG originalmente
                format_name = 'PNG' if image_file.content_type == 'image/png' else 'JPEG'
                if format_name == 'JPEG':
                    image.save(output, format='JPEG', quality=90, optimize=True)
                    output.content_type = 'image/jpeg'
                else:
                    image.save(output, format='PNG', optimize=True)
                    output.content_type = 'image/png'
            
            output.seek(0)
            return output
            
        except Exception as e:
            logger.error(f"❌ Error procesando imagen: {e}")
            raise e
    
    def process_multiple_images(self, image_files):
        """
        Procesar múltiples imágenes
        """
        processed_files = []
        
        for image_file in image_files:
            if image_file and image_file.filename != '':
                if self.is_allowed_file(image_file.filename):
                    try:
                        processed_file = self.resize_image(image_file)
                        processed_file.filename = image_file.filename
                        processed_files.append(processed_file)
                    except Exception as e:
                        logger.error(f"❌ Error procesando {image_file.filename}: {e}")
                        continue
                else:
                    logger.warning(f"⚠️ Archivo no permitido: {image_file.filename}")
        
        return processed_files
    
    def validate_image_files(self, files):
        """
        Validar que todos los archivos sean imágenes válidas
        """
        valid_files = []
        errors = []
        
        for file in files:
            if file and file.filename != '':
                if not self.is_allowed_file(file.filename):
                    errors.append(f"Formato no permitido: {file.filename}")
                    continue
                
                try:
                    # Intentar abrir la imagen para validar
                    file.seek(0)  # Resetear posición
                    Image.open(file)
                    file.seek(0)  # Resetear para uso posterior
                    valid_files.append(file)
                except Exception as e:
                    errors.append(f"Imagen corrupta: {file.filename}")
        
        return valid_files, errors

# Instancia global del procesador de imágenes
image_processor = ImageProcessor() 