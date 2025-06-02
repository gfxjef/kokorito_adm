# 🔧 Configuración AWS S3 para Kokorito

## 📋 Configuración Requerida del Bucket S3

### 1. Política del Bucket (Bucket Policy)

Ve a tu bucket S3 en AWS Console → Permissions → Bucket Policy y agrega esta política:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::redkossodo/*"
    }
  ]
}
```

**Importante**: Reemplaza `redkossodo` con el nombre real de tu bucket.

### 2. Configuración CORS

Ve a tu bucket S3 → Permissions → Cross-origin resource sharing (CORS):

```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "HEAD", "PUT", "POST"],
        "AllowedOrigins": ["*"],
        "ExposeHeaders": ["Content-Length", "Content-Type", "Content-Disposition"],
        "MaxAgeSeconds": 3000
    }
]
```

### 3. Block Public Access Settings

Ve a tu bucket S3 → Permissions → Block public access (bucket settings):

- ✅ **Block public access to buckets and objects granted through new access control lists (ACLs)**: ON
- ✅ **Block public access to buckets and objects granted through any access control lists (ACLs)**: ON  
- ❌ **Block public access to buckets and objects granted through new public bucket or access point policies**: OFF
- ❌ **Block public and cross-account access to buckets and objects through any public bucket or access point policies**: OFF

### 4. Verificación de Acceso

Para verificar que la configuración funciona:

1. Sube un archivo de prueba manualmente al bucket
2. Accede a la URL: `https://redkossodo.s3.us-east-2.amazonaws.com/test-file.jpg`
3. Debe mostrarse la imagen sin errores

## 🚀 Estructura de Archivos

El sistema organizará los archivos así:

```
redkossodo/
└── productos/
    ├── imagen_producto_20241201_143022_a1b2c3d4.jpg
    ├── torta_chocolate_20241201_143045_e5f6g7h8.png
    └── promocion_especial_20241201_143067_i9j0k1l2.webp
```

## ⚠️ Troubleshooting

### Error: AccessControlListNotSupported
- **Causa**: El bucket tiene bloqueados los ACLs pero el código intenta usarlos
- **Solución**: ✅ Ya corregido en el nuevo `s3_handler.py` - no usa ACLs

### Error: Access Denied
- **Causa**: Política del bucket no configurada o incorrecta
- **Solución**: Aplicar la política del paso 1

### Error: CORS
- **Causa**: Configuración CORS faltante
- **Solución**: Aplicar configuración CORS del paso 2

## 🔍 Verificación Final

Después de aplicar la configuración, prueba subir una imagen desde el sistema:

1. Ve a `http://localhost:5000/products/add`
2. Selecciona "Personal" 
3. Completa el formulario
4. Sube una imagen
5. Debe subir exitosamente y mostrar mensaje de éxito 