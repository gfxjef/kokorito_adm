# 🍰 Kokorito Admin - Sistema de Administración de Productos

Sistema web completo para administrar productos de repostería con integración a AWS S3, MySQL y interfaz 100% responsive.

## 🚀 Características

- ✅ **4 Tipos de Productos**: Personal, Molde Rectangular, Molde Circular, Promociones
- ✅ **Subida de Imágenes**: AWS S3 con redimensionamiento automático (máx. 1200px)
- ✅ **100% Responsive**: Optimizado para móviles
- ✅ **Base de Datos MySQL**: Creación automática de tablas
- ✅ **Toggle Disponibilidad**: Activar/desactivar productos
- ✅ **CRUD Completo**: Crear, editar, eliminar productos
- ✅ **Búsqueda y Filtros**: Buscar por nombre, categoría, disponibilidad
- ✅ **Operaciones Masivas**: Activar/desactivar múltiples productos
- ✅ **Interfaz Moderna**: Tailwind CSS con animaciones

## 📋 Requisitos

- Python 3.8+
- MySQL 5.7+
- Cuenta AWS con acceso a S3

## 🛠️ Instalación

### 1. Clonar el repositorio
```bash
git clone <repository-url>
cd kokorito
```

### 2. Crear entorno virtual
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
Crear archivo `.env` en la raíz del proyecto:

```env
# AWS S3 Configuration
AWS_ACCESS_KEY_ID=tu_access_key_id
AWS_SECRET_ACCESS_KEY=tu_secret_access_key
AWS_DEFAULT_REGION=us-east-2
S3_BUCKET=tu_bucket_name

# MySQL Database Configuration
DB_HOST=tu_host_mysql
DB_NAME=tu_base_de_datos
DB_USER=tu_usuario
DB_PASSWORD=tu_contraseña
DB_PORT=3306

# Flask Configuration
FLASK_ENV=development
SECRET_KEY=tu_clave_secreta_aqui
```

### 5. Configurar AWS S3
1. Crear bucket en AWS S3
2. Configurar permisos públicos para lectura
3. Actualizar CORS policy si es necesario

### 6. Ejecutar la aplicación
```bash
python app.py
```

La aplicación estará disponible en: `http://localhost:5000`

## 📚 Estructura del Proyecto

```
kokorito/
├── app.py                 # Aplicación Flask principal
├── config.py             # Configuración y variables de entorno
├── requirements.txt      # Dependencias Python
├── .env                 # Variables de entorno (crear manualmente)
├── models/
│   └── database.py      # Modelos y conexión MySQL
├── routes/
│   ├── products.py      # Rutas CRUD productos
│   └── admin.py         # Rutas de administración
├── utils/
│   ├── s3_handler.py    # Manejo AWS S3
│   └── image_processor.py # Procesamiento imágenes
├── static/
│   ├── js/
│   │   └── app.js       # JavaScript frontend
│   └── css/            # Estilos adicionales
└── templates/
    ├── base.html        # Template base
    ├── index.html       # Página principal
    ├── add_product.html # Agregar producto
    └── manage.html      # Administrar productos
```

## 🗃️ Base de Datos

El sistema crea automáticamente las siguientes tablas:

### `kok_personal`
- `id` (AUTO_INCREMENT)
- `nombre` (VARCHAR, NOT NULL)
- `descripcion` (TEXT, NOT NULL)
- `sabor` (VARCHAR, NOT NULL)
- `categoria` (VARCHAR, NOT NULL)
- `imagen` (TEXT, NOT NULL) - URLs separadas por coma
- `precio` (DECIMAL, NOT NULL)
- `disponible` (BOOLEAN, DEFAULT TRUE)
- `created_at` (TIMESTAMP)

### `kok_molde_rect`
- Mismos campos que `kok_personal` +
- `porciones` (INT, NOT NULL)

### `kok_molde_circular`
- Mismos campos que `kok_molde_rect` +
- `tamaño_molde` (DECIMAL, NOT NULL)

### `kok_promo`
- `id`, `nombre`, `descripcion`, `categoria`, `imagen`, `precio`, `disponible`, `created_at`

## 🎯 Uso del Sistema

### Página Principal
- Dashboard con estadísticas rápidas
- Acceso directo a "Agregar Producto" y "Administrar Productos"

### Agregar Productos
1. Seleccionar tipo de producto
2. Completar formulario dinámico (campos cambian según tipo)
3. Subir imágenes (drag & drop o clic)
4. Guardar producto

### Administrar Productos
1. Seleccionar tipo de producto del dropdown
2. Usar filtros de búsqueda y disponibilidad
3. Toggle individual o masivo de disponibilidad
4. Editar o eliminar productos

## 🔧 API Endpoints

### Productos
- `GET /products/add` - Página agregar producto
- `POST /products/add` - Crear nuevo producto
- `PUT /products/edit/<type>/<id>` - Editar producto
- `DELETE /products/delete/<type>/<id>` - Eliminar producto
- `POST /products/toggle/<type>/<id>` - Toggle disponibilidad

### Administración
- `GET /admin/manage` - Página administrar productos
- `GET /admin/products/<type>` - Listar productos por tipo
- `GET /admin/product/<type>/<id>` - Obtener producto específico
- `GET /admin/stats` - Estadísticas generales
- `GET /admin/search` - Buscar productos
- `POST /admin/bulk-toggle` - Operaciones masivas

## 🎨 Frontend

- **Framework CSS**: Tailwind CSS (CDN)
- **JavaScript**: Vanilla JS con clases ES6
- **Iconos**: FontAwesome
- **Funcionalidades**:
  - Drag & drop para imágenes
  - Formularios dinámicos
  - Toggle switches animados
  - Notificaciones toast
  - Loading overlays
  - Paginación
  - Búsqueda en tiempo real

## 🖼️ Manejo de Imágenes

- **Formatos permitidos**: JPG, PNG, WEBP
- **Redimensionamiento**: Automático a máximo 1200px ancho
- **Almacenamiento**: AWS S3
- **Múltiples imágenes**: Separadas por coma en BD
- **Validación**: Tipo, tamaño y formato

## 📱 Responsive Design

- **Mobile-first**: Optimizado para dispositivos móviles
- **Breakpoints**: sm, md, lg, xl
- **Navegación**: Menú hamburguesa en móvil
- **Grid responsivo**: 1 columna móvil, 2-3 columnas escritorio
- **Touch-friendly**: Botones y áreas táctiles grandes

## 🛡️ Seguridad

- Validación de tipos de archivo
- Sanitización de inputs
- Protección CSRF (Flask integrado)
- Validación server-side
- Manejo seguro de errores

## 🚨 Troubleshooting

### Error de conexión a MySQL
```bash
# Verificar credenciales en .env
# Verificar que MySQL esté ejecutándose
# Verificar permisos de usuario
```

### Error de AWS S3
```bash
# Verificar credentials en .env
# Verificar permisos del bucket
# Verificar política CORS
```

### Error de dependencias
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

## 🔄 Desarrollo

### Agregar nuevos tipos de producto
1. Actualizar `TABLE_MAPPING` en routes
2. Agregar tabla en `database.py`
3. Actualizar formulario en `add_product.html`
4. Actualizar JavaScript en `app.js`

### Customizar estilos
- Modificar colores en `base.html` (Tailwind config)
- Agregar CSS custom en `static/css/`

## 📄 Licencia

Este proyecto está bajo la Licencia MIT.

## 👨‍💻 Autor

Desarrollado para Kokorito - Sistema de administración de productos de repostería.

---

¿Necesitas ayuda? Revisa la documentación o contacta al desarrollador. 