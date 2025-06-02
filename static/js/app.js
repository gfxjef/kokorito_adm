/**
 * Kokorito Admin - Frontend JavaScript
 * Maneja toda la lógica interactiva del sistema de administración
 */

// Configuración global
const CONFIG = {
    API_BASE: '',
    TOAST_DURATION: 5000,
    LOADING_DELAY: 300,
    IMAGE_MAX_SIZE: 5 * 1024 * 1024, // 5MB
    ALLOWED_EXTENSIONS: ['jpg', 'jpeg', 'png', 'webp']
};

// Estado global de la aplicación
const AppState = {
    currentProductType: null,
    currentPage: 1,
    selectedProducts: new Set(),
    isLoading: false,
    searchTimeout: null
};

/**
 * UTILITY FUNCTIONS
 */

// Mostrar/ocultar loading overlay
function showLoading() {
    document.getElementById('loading-overlay')?.classList.remove('hidden');
    AppState.isLoading = true;
}

function hideLoading() {
    document.getElementById('loading-overlay')?.classList.add('hidden');
    AppState.isLoading = false;
}

// Sistema de notificaciones toast
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) return;
    
    const toast = document.createElement('div');
    const id = Date.now();
    
    const bgColors = {
        'success': 'bg-green-500',
        'error': 'bg-red-500',
        'warning': 'bg-yellow-500',
        'info': 'bg-blue-500'
    };
    
    const icons = {
        'success': 'fas fa-check-circle',
        'error': 'fas fa-exclamation-circle',
        'warning': 'fas fa-exclamation-triangle',
        'info': 'fas fa-info-circle'
    };
    
    toast.id = `toast-${id}`;
    toast.className = `${bgColors[type] || bgColors.info} text-white px-6 py-4 rounded-lg shadow-lg flex items-center space-x-3 transform transition-all duration-300 translate-x-full`;
    toast.innerHTML = `
        <i class="${icons[type] || icons.info}"></i>
        <span class="flex-1">${message}</span>
        <button onclick="removeToast('${id}')" class="text-white hover:text-gray-200 ml-4">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    toastContainer.appendChild(toast);
    
    // Animar entrada
    setTimeout(() => toast.classList.remove('translate-x-full'), 100);
    
    // Auto-remover
    setTimeout(() => removeToast(id), CONFIG.TOAST_DURATION);
}

function removeToast(id) {
    const toast = document.getElementById(`toast-${id}`);
    if (toast) {
        toast.classList.add('translate-x-full');
        setTimeout(() => toast.remove(), 300);
    }
}

// Diálogo de confirmación
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Manejo de respuestas fetch
async function handleResponse(response) {
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }
    return response.json();
}

// Validador de archivos de imagen
function validateImageFile(file) {
    const errors = [];
    
    // Verificar tipo
    if (!file.type.startsWith('image/')) {
        errors.push(`${file.name}: No es una imagen válida`);
    }
    
    // Verificar extensión
    const extension = file.name.split('.').pop().toLowerCase();
    if (!CONFIG.ALLOWED_EXTENSIONS.includes(extension)) {
        errors.push(`${file.name}: Formato no permitido. Use: ${CONFIG.ALLOWED_EXTENSIONS.join(', ')}`);
    }
    
    // Verificar tamaño
    if (file.size > CONFIG.IMAGE_MAX_SIZE) {
        errors.push(`${file.name}: Archivo muy grande. Máximo 5MB`);
    }
    
    return errors;
}

/**
 * FORM HANDLERS
 */

// Manejador de formulario de productos
class ProductFormHandler {
    constructor(formId) {
        this.form = document.getElementById(formId);
        this.selectedFiles = [];
        this.productType = null;
        
        if (this.form) {
            this.init();
        }
    }
    
    init() {
        this.setupProductTypeSelection();
        this.setupImageUpload();
        this.setupFormSubmission();
    }
    
    setupProductTypeSelection() {
        const typeOptions = document.querySelectorAll('.product-type-option');
        
        typeOptions.forEach(option => {
            option.addEventListener('click', (e) => {
                const radio = option.querySelector('input[type="radio"]');
                const div = option.querySelector('div');
                
                // Reset all options
                typeOptions.forEach(opt => {
                    const optDiv = opt.querySelector('div');
                    optDiv.classList.remove('border-kokorito-500', 'bg-kokorito-50');
                    optDiv.classList.add('border-gray-200');
                });
                
                // Select current option
                radio.checked = true;
                div.classList.remove('border-gray-200');
                div.classList.add('border-kokorito-500', 'bg-kokorito-50');
                
                this.productType = radio.value;
                this.showFormFields(this.productType);
                this.form.style.display = 'block';
                this.form.scrollIntoView({ behavior: 'smooth' });
            });
        });
    }
    
    showFormFields(productType) {
        // Ocultar todos los campos condicionales
        const conditionalFields = ['sabor-field', 'porciones-field', 'tamano-molde-field'];
        conditionalFields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) {
                field.style.display = 'none';
                const input = field.querySelector('input');
                if (input) input.required = false;
            }
        });
        
        // Mostrar campos según tipo de producto
        const fieldMappings = {
            'personal': ['sabor-field'],
            'molde_rect': ['sabor-field', 'porciones-field'],
            'molde_circular': ['sabor-field', 'porciones-field', 'tamano-molde-field'],
            'promo': []
        };
        
        const fieldsToShow = fieldMappings[productType] || [];
        fieldsToShow.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) {
                field.style.display = 'block';
                const input = field.querySelector('input');
                if (input) input.required = true;
            }
        });
    }
    
    setupImageUpload() {
        const uploadArea = document.getElementById('image-upload-area');
        const fileInput = document.getElementById('images');
        const preview = document.getElementById('image-preview');
        const placeholder = document.getElementById('upload-placeholder');
        
        if (!uploadArea || !fileInput) return;
        
        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('drag-over');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('drag-over');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');
            this.handleFiles(Array.from(e.dataTransfer.files));
        });
        
        fileInput.addEventListener('change', (e) => {
            this.handleFiles(Array.from(e.target.files));
        });
    }
    
    handleFiles(files) {
        const validFiles = [];
        const errors = [];
        
        files.forEach(file => {
            const fileErrors = validateImageFile(file);
            if (fileErrors.length === 0) {
                validFiles.push(file);
            } else {
                errors.push(...fileErrors);
            }
        });
        
        if (errors.length > 0) {
            showToast(`Errores en archivos:\n${errors.join('\n')}`, 'error');
        }
        
        if (validFiles.length > 0) {
            this.selectedFiles = validFiles;
            this.showImagePreview();
        }
    }
    
    showImagePreview() {
        const preview = document.getElementById('image-preview');
        const placeholder = document.getElementById('upload-placeholder');
        
        if (!preview || !placeholder) return;
        
        placeholder.classList.add('hidden');
        preview.classList.remove('hidden');
        preview.innerHTML = '';
        
        this.selectedFiles.forEach((file, index) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                const div = document.createElement('div');
                div.className = 'relative group';
                div.innerHTML = `
                    <img src="${e.target.result}" class="w-full h-24 object-cover rounded-lg">
                    <button type="button" onclick="productFormHandler.removeImage(${index})" 
                            class="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                        <i class="fas fa-times text-xs"></i>
                    </button>
                    <div class="absolute bottom-0 left-0 right-0 bg-black bg-opacity-50 text-white text-xs p-1 rounded-b-lg truncate">
                        ${file.name}
                    </div>
                `;
                preview.appendChild(div);
            };
            reader.readAsDataURL(file);
        });
    }
    
    removeImage(index) {
        this.selectedFiles.splice(index, 1);
        if (this.selectedFiles.length > 0) {
            this.showImagePreview();
        } else {
            document.getElementById('upload-placeholder')?.classList.remove('hidden');
            document.getElementById('image-preview')?.classList.add('hidden');
        }
    }
    
    setupFormSubmission() {
        this.form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            if (!this.validateForm()) return;
            
            showLoading();
            
            try {
                const formData = this.buildFormData();
                const response = await fetch('/products/add', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await handleResponse(response);
                
                showToast('Producto agregado exitosamente', 'success');
                setTimeout(() => {
                    window.location.href = '/admin/manage';
                }, 1500);
                
            } catch (error) {
                console.error('Error:', error);
                showToast(error.message || 'Error agregando producto', 'error');
            } finally {
                hideLoading();
            }
        });
    }
    
    validateForm() {
        if (!this.productType) {
            showToast('Por favor selecciona un tipo de producto', 'error');
            return false;
        }
        
        if (this.selectedFiles.length === 0) {
            showToast('Por favor selecciona al menos una imagen', 'error');
            return false;
        }
        
        // Validar campos requeridos
        const requiredFields = this.form.querySelectorAll('input[required], textarea[required]');
        for (let field of requiredFields) {
            if (!field.value.trim()) {
                showToast(`El campo "${field.previousElementSibling.textContent}" es requerido`, 'error');
                field.focus();
                return false;
            }
        }
        
        return true;
    }
    
    buildFormData() {
        const formData = new FormData();
        formData.append('product_type', this.productType);
        
        // Agregar campos del formulario
        const inputs = this.form.querySelectorAll('input:not([type="file"]), textarea, select');
        inputs.forEach(input => {
            if (input.name && input.value) {
                formData.append(input.name, input.value);
            }
        });
        
        // Agregar imágenes
        this.selectedFiles.forEach(file => {
            formData.append('images', file);
        });
        
        return formData;
    }
}

/**
 * PRODUCT MANAGEMENT
 */

class ProductManager {
    constructor() {
        this.currentProductType = null;
        this.currentPage = 1;
        this.selectedProducts = new Set();
        this.allProducts = [];
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Selector de tipo de producto
        const typeSelect = document.getElementById('product-type-select');
        if (typeSelect) {
            typeSelect.addEventListener('change', (e) => {
                this.currentProductType = e.target.value;
                this.currentPage = 1;
                this.selectedProducts.clear();
                
                if (this.currentProductType) {
                    this.loadProducts();
                } else {
                    this.showPlaceholder();
                }
            });
        }
        
        // Búsqueda
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                clearTimeout(AppState.searchTimeout);
                AppState.searchTimeout = setTimeout(() => {
                    this.currentPage = 1;
                    if (this.currentProductType) this.loadProducts();
                }, 500);
            });
        }
        
        // Filtro de disponibilidad
        const availabilityFilter = document.getElementById('availability-filter');
        if (availabilityFilter) {
            availabilityFilter.addEventListener('change', () => {
                this.currentPage = 1;
                if (this.currentProductType) this.loadProducts();
            });
        }
        
        // Seleccionar todos
        const selectAll = document.getElementById('select-all');
        if (selectAll) {
            selectAll.addEventListener('change', (e) => {
                const checkboxes = document.querySelectorAll('.product-checkbox');
                checkboxes.forEach(cb => {
                    cb.checked = e.target.checked;
                    const productId = parseInt(cb.value);
                    if (e.target.checked) {
                        this.selectedProducts.add(productId);
                    } else {
                        this.selectedProducts.delete(productId);
                    }
                });
                this.updateBulkActions();
            });
        }
        
        // Acciones masivas
        document.getElementById('bulk-activate-btn')?.addEventListener('click', () => this.bulkToggle(true));
        document.getElementById('bulk-deactivate-btn')?.addEventListener('click', () => this.bulkToggle(false));
    }
    
    async loadProducts() {
        if (!this.currentProductType) return;
        
        this.showLoading();
        
        try {
            const params = new URLSearchParams({
                page: this.currentPage,
                per_page: 12,
                search: document.getElementById('search-input')?.value || '',
                disponible: document.getElementById('availability-filter')?.value || ''
            });
            
            const response = await fetch(`/admin/products/${this.currentProductType}?${params}`);
            const data = await handleResponse(response);
            
            this.allProducts = data.products;
            this.displayProducts(data.products);
            this.displayPagination(data.pagination);
            this.updateStats();
            this.showProductsGrid();
            
        } catch (error) {
            console.error('Error:', error);
            showToast(error.message || 'Error cargando productos', 'error');
        } finally {
            this.hideLoading();
        }
    }
    
    displayProducts(products) {
        const container = document.getElementById('products-list');
        if (!container) return;
        
        if (products.length === 0) {
            this.showNoProducts();
            return;
        }
        
        container.innerHTML = products.map(product => this.createProductCard(product)).join('');
    }
    
    createProductCard(product) {
        const isChecked = this.selectedProducts.has(product.id);
        const statusColor = product.disponible ? 'text-green-600' : 'text-red-600';
        const statusIcon = product.disponible ? 'fa-check-circle' : 'fa-times-circle';
        const mainImage = product.imagen_list?.[0] || '';
        
        return `
            <div class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div class="flex items-center mb-3">
                    <input type="checkbox" class="product-checkbox rounded border-gray-300 text-kokorito-600 focus:ring-kokorito-500" 
                           value="${product.id}" ${isChecked ? 'checked' : ''} 
                           onchange="productManager.toggleProductSelection(${product.id})">
                    <span class="ml-2 text-sm text-gray-600">#${product.id}</span>
                    <i class="fas ${statusIcon} ${statusColor} ml-auto"></i>
                </div>
                
                ${mainImage ? `
                    <img src="${mainImage}" alt="${product.nombre}" class="w-full h-32 object-cover rounded-lg mb-3">
                ` : `
                    <div class="w-full h-32 bg-gray-200 rounded-lg mb-3 flex items-center justify-center">
                        <i class="fas fa-image text-gray-400 text-2xl"></i>
                    </div>
                `}
                
                <h4 class="font-semibold text-gray-900 mb-2 truncate">${product.nombre}</h4>
                <p class="text-sm text-gray-600 mb-2 line-clamp-2">${product.descripcion}</p>
                
                <div class="text-xs text-gray-500 mb-3 space-y-1">
                    <div><strong>Categoría:</strong> ${product.categoria}</div>
                    ${product.sabor ? `<div><strong>Sabor:</strong> ${product.sabor}</div>` : ''}
                    ${product.porciones ? `<div><strong>Porciones:</strong> ${product.porciones}</div>` : ''}
                    ${product.tamaño_molde ? `<div><strong>Tamaño:</strong> ${product.tamaño_molde} cm</div>` : ''}
                </div>
                
                <div class="text-lg font-bold text-kokorito-600 mb-4">$${parseFloat(product.precio).toFixed(2)}</div>
                
                <div class="flex justify-between items-center">
                    <label class="toggle-switch">
                        <input type="checkbox" ${product.disponible ? 'checked' : ''} 
                               onchange="productManager.toggleAvailability('${this.currentProductType}', ${product.id})">
                        <span class="slider"></span>
                    </label>
                    
                    <div class="flex space-x-2">
                        <button onclick="productManager.editProduct('${this.currentProductType}', ${product.id})" 
                                class="p-2 text-blue-600 hover:bg-blue-50 rounded-md transition-colors">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button onclick="productManager.deleteProduct('${this.currentProductType}', ${product.id}, '${product.nombre}')" 
                                class="p-2 text-red-600 hover:bg-red-50 rounded-md transition-colors">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    async toggleAvailability(productType, productId) {
        try {
            const response = await fetch(`/products/toggle/${productType}/${productId}`, {
                method: 'POST'
            });
            
            const data = await handleResponse(response);
            showToast(data.message, 'success');
            this.loadProducts();
            
        } catch (error) {
            console.error('Error:', error);
            showToast(error.message || 'Error cambiando disponibilidad', 'error');
            this.loadProducts();
        }
    }
    
    async deleteProduct(productType, productId, productName) {
        confirmAction(`¿Estás seguro de eliminar "${productName}"? Esta acción no se puede deshacer.`, async () => {
            try {
                const response = await fetch(`/products/delete/${productType}/${productId}`, {
                    method: 'DELETE'
                });
                
                const data = await handleResponse(response);
                showToast(data.message, 'success');
                this.selectedProducts.delete(productId);
                this.loadProducts();
                
            } catch (error) {
                console.error('Error:', error);
                showToast(error.message || 'Error eliminando producto', 'error');
            }
        });
    }
    
    toggleProductSelection(productId) {
        if (this.selectedProducts.has(productId)) {
            this.selectedProducts.delete(productId);
        } else {
            this.selectedProducts.add(productId);
        }
        this.updateBulkActions();
        this.updateStats();
    }
    
    updateBulkActions() {
        const activateBtn = document.getElementById('bulk-activate-btn');
        const deactivateBtn = document.getElementById('bulk-deactivate-btn');
        
        if (this.selectedProducts.size > 0) {
            activateBtn?.classList.remove('hidden');
            deactivateBtn?.classList.remove('hidden');
        } else {
            activateBtn?.classList.add('hidden');
            deactivateBtn?.classList.add('hidden');
        }
    }
    
    async bulkToggle(newStatus) {
        if (this.selectedProducts.size === 0) return;
        
        const action = newStatus ? 'activar' : 'desactivar';
        confirmAction(`¿Estás seguro de ${action} ${this.selectedProducts.size} producto(s)?`, async () => {
            try {
                const response = await fetch('/admin/bulk-toggle', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        product_type: this.currentProductType,
                        product_ids: Array.from(this.selectedProducts),
                        available: newStatus
                    })
                });
                
                const data = await handleResponse(response);
                showToast(data.message, 'success');
                this.selectedProducts.clear();
                document.getElementById('select-all').checked = false;
                this.loadProducts();
                
            } catch (error) {
                console.error('Error:', error);
                showToast(error.message || 'Error en operación masiva', 'error');
            }
        });
    }
    
    editProduct(productType, productId) {
        showToast('Función de edición en desarrollo', 'info');
    }
    
    updateStats() {
        const statsContainer = document.getElementById('current-stats');
        if (!statsContainer) return;
        
        const total = this.allProducts.length;
        const available = this.allProducts.filter(p => p.disponible).length;
        const unavailable = total - available;
        
        statsContainer.innerHTML = `
            <div class="text-center">
                <div class="text-2xl font-bold text-gray-900">${total}</div>
                <div class="text-sm text-gray-600">Total</div>
            </div>
            <div class="text-center">
                <div class="text-2xl font-bold text-green-600">${available}</div>
                <div class="text-sm text-gray-600">Disponibles</div>
            </div>
            <div class="text-center">
                <div class="text-2xl font-bold text-red-600">${unavailable}</div>
                <div class="text-sm text-gray-600">No Disponibles</div>
            </div>
            <div class="text-center">
                <div class="text-2xl font-bold text-kokorito-600">${this.selectedProducts.size}</div>
                <div class="text-sm text-gray-600">Seleccionados</div>
            </div>
        `;
    }
    
    showLoading() {
        document.getElementById('products-loading')?.classList.remove('hidden');
        document.getElementById('products-grid')?.classList.add('hidden');
        document.getElementById('no-products')?.classList.add('hidden');
        document.getElementById('products-placeholder')?.classList.add('hidden');
    }
    
    hideLoading() {
        document.getElementById('products-loading')?.classList.add('hidden');
    }
    
    showProductsGrid() {
        document.getElementById('products-grid')?.classList.remove('hidden');
        document.getElementById('products-placeholder')?.classList.add('hidden');
        document.getElementById('no-products')?.classList.add('hidden');
        document.getElementById('stats-panel')?.classList.remove('hidden');
        
        const titleMap = {
            'personal': 'Productos Personales',
            'molde_rect': 'Moldes Rectangulares',
            'molde_circular': 'Moldes Circulares',
            'promo': 'Promociones'
        };
        
        const titleElement = document.getElementById('products-title');
        if (titleElement) {
            titleElement.textContent = titleMap[this.currentProductType] || 'Productos';
        }
    }
    
    showNoProducts() {
        document.getElementById('no-products')?.classList.remove('hidden');
        document.getElementById('products-grid')?.classList.add('hidden');
    }
    
    showPlaceholder() {
        document.getElementById('products-placeholder')?.classList.remove('hidden');
        document.getElementById('products-grid')?.classList.add('hidden');
        document.getElementById('no-products')?.classList.add('hidden');
        document.getElementById('stats-panel')?.classList.add('hidden');
    }
}

/**
 * INITIALIZATION
 */

// Variables globales para acceso desde HTML
let productFormHandler = null;
let productManager = null;

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar componentes según la página
    if (document.getElementById('product-form')) {
        productFormHandler = new ProductFormHandler('product-form');
    }
    
    if (document.getElementById('product-type-select')) {
        productManager = new ProductManager();
    }
    
    // Cargar estadísticas en página principal
    if (document.getElementById('stats-container')) {
        loadHomeStats();
    }
});

// Cargar estadísticas para la página principal
async function loadHomeStats() {
    try {
        const response = await fetch('/admin/stats');
        const data = await handleResponse(response);
        
        const statsContainer = document.getElementById('stats-container');
        if (statsContainer && data.general_stats) {
            const stats = data.general_stats;
            statsContainer.innerHTML = `
                <div class="text-center">
                    <div class="text-2xl font-bold text-gray-900">${stats.total_products}</div>
                    <div class="text-sm text-gray-600">Total Productos</div>
                </div>
                <div class="text-center">
                    <div class="text-2xl font-bold text-green-600">${stats.total_available}</div>
                    <div class="text-sm text-gray-600">Disponibles</div>
                </div>
                <div class="text-center">
                    <div class="text-2xl font-bold text-red-600">${stats.total_unavailable}</div>
                    <div class="text-sm text-gray-600">No Disponibles</div>
                </div>
                <div class="text-center">
                    <div class="text-2xl font-bold text-kokorito-600">4</div>
                    <div class="text-sm text-gray-600">Categorías</div>
                </div>
            `;
        }
    } catch (error) {
        console.log('Error loading stats:', error);
    }
} 