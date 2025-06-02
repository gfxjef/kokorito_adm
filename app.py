from flask import Flask, render_template
from flask_cors import CORS
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Importar rutas
from routes.products import products_bp
from routes.admin import admin_bp

# Registrar blueprints
app.register_blueprint(products_bp)
app.register_blueprint(admin_bp)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    # Inicializar base de datos al arrancar
    try:
        from models.database import db
        print("✅ Base de datos inicializada correctamente")
    except Exception as e:
        print(f"❌ Error inicializando base de datos: {e}")
    
    app.run(debug=True, host='0.0.0.0', port=5000) 