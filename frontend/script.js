// Configuración de la API
const API_BASE_URL = 'http://localhost:5000/api';
// Sets para almacenar los seleccionados
const selectedCategories = new Set();
const selectedTags = new Set();
// configurar path para las páginas, probando cosas...
const path = window.location.pathname;


// Función genérica para renderizar la lista
// Función genérica para renderizar la lista
function renderSelectableList(containerId, items, selectedSet) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';

    // Verificar que items sea un array
    if (!items || !Array.isArray(items)) {
        console.error(`Items no es un array para ${containerId}:`, items);
        container.innerHTML = `<p class="no-items">Error al cargar elementos</p>`;
        return;
    }

    if (items.length === 0) {
        container.innerHTML = `<p class="no-items">No hay elementos disponibles</p>`;
        return;
    }

    items.forEach(item => {
        const el = document.createElement('div');
        el.className = 'selectable-item';
        
        // Manejar diferentes estructuras de datos
        const displayText = item.category_name || item.tname || item.name || item.tagurl || item.url_cat || 'Desconocido';
        el.textContent = displayText;

        // Usar el ID correcto según la estructura
        const itemId = item._id || item.id;
        
        if (!itemId) {
            console.warn('Item sin ID:', item);
            return; // Saltar items sin ID
        }

        el.addEventListener('click', () => {
            if (selectedSet.has(itemId)) {
                selectedSet.delete(itemId);
                el.classList.remove('selected');
            } else {
                selectedSet.add(itemId);
                el.classList.add('selected');
            }
        });

        container.appendChild(el);
    });
}

// Función para mostrar mensajes al usuario
function showMessage(message, type = 'info') {
    const messageEl = document.createElement('div');
    messageEl.className = `message message-${type}`;
    messageEl.textContent = message;
    
    messageEl.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 4px;
        color: white;
        z-index: 1000;
        max-width: 300px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    `;
    
    if (type === 'success') {
        messageEl.style.backgroundColor = '#28a745';
    } else if (type === 'error') {
        messageEl.style.backgroundColor = '#dc3545';
    } else {
        messageEl.style.backgroundColor = '#17a2b8';
    }
    
    document.body.appendChild(messageEl);
    
    setTimeout(() => {
        messageEl.remove();
    }, 3000);
}

// Función para hacer peticiones a la API
// Función para hacer peticiones a la API
async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            let errorMessage = 'Error en la petición';
            try {
                const errorData = await response.json();
                errorMessage = errorData.error || errorMessage;
            } catch (e) {
                errorMessage = `HTTP ${response.status}: ${response.statusText}`;
            }
            throw new Error(errorMessage);
        }
        
        // Solo intenta parsear JSON si hay contenido
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.indexOf("application/json") !== -1) {
            return await response.json();
        }
        return {}; // Devuelve un objeto vacío si no hay JSON

    } catch (error) {
        console.error('Error en API call:', error);
        showMessage(error.message, 'error');
        throw error;
    }
}
// Funciones para obtener datos desde la API
async function loadTags() {
    try {
        const response = await fetch(`${API_BASE_URL}/tags/ids`);
        console.log("Response status:", response.status);
        console.log("Response ok:", response.ok);
        
        const data = await response.json();
        console.log("Tags data:", data);
        console.log("Type of data:", typeof data);
        console.log("Is array?", Array.isArray(data));
        
        renderSelectableList('tags-container', data, selectedTags);
    } catch (error) {
        console.error('Error al cargar los tags:', error);
        showMessage('Error al cargar los tags', 'error');
    }
}

async function loadCategorias() {
    try {
        const response = await fetch(`${API_BASE_URL}/categorias/ids`);
        console.log("Categorias response status:", response.status);
        
        const data = await response.json();
        console.log("Categorias data:", data);
        console.log("Type of categorias data:", typeof data);
        
        renderSelectableList('categories-container', data, selectedCategories);
    } catch (error) {
        console.error('Error al cargar las categorías:', error);
        showMessage('Error al cargar las categorías', 'error');
    }
}

// Función para cargar datos reales desde la API
async function loadRealData() {
    try {
        // Cargar artículos
        if (path.includes("articulos.html")) {
            const articulos = await apiCall('/articulos');
            const tbody = document.querySelector('#articles-table tbody');
            tbody.innerHTML = '';
            
        articulos.forEach(articulo => {
            const tr = document.createElement('tr');
            
            // Crear elementos para tags y categorías
            console.log(articulos)
            const tagsHTML = articulo.tags && articulo.tags.length > 0 
                ? `<div class="tags-container">${articulo.tags.map(tag => `<a href=articulos_tag.html?tag=${encodeURIComponent(tag.tname)} class="tag-pill">${tag.tname}</a>`).join('')}</div>`
                : '<span style="color: var(--text-color-secondary); font-style: italic;">Sin tags</span>';
            
            const categoriesHTML = articulo.categories && articulo.categories.length > 0 
                ? `<div class="categories-container">${articulo.categories.map(cat => `<a href=articulos_categoria.html?categoria=${encodeURIComponent(cat.cname)} class="category-pill">${cat.cname}</a>`).join('')}</div>`
                : '<span style="color: var(--text-color-secondary); font-style: italic;">Sin categorías</span>';

            tr.innerHTML = `
                <td>${articulo.articulo_id}</td>
                <td>${articulo.user_name} (ID: ${articulo.user_id})</td>
                <td>
                    <strong>${articulo.titulo}</strong>
                    <div class="article-details">
                        ${articulo.content ? articulo.content.substring(0, 100) + (articulo.content.length > 100 ? '...' : '') : 'Sin contenido'}
                    </div>
                    <div class="comments-section">
                        <button class="comments-toggle" onclick="toggleComments(${articulo.articulo_id})">
                            💬 Ver comentarios
                        </button>
                        <div id="comments-${articulo.articulo_id}" class="comments-container"></div>
                    </div>
                </td>
                <td>
                    <div><strong>Tags:</strong> ${tagsHTML}</div>
                    <div style="margin-top: 0.5rem;"><strong>Categorías:</strong> ${categoriesHTML}</div>
                </td>
                <td class="action-buttons">
                    <button class="btn btn-danger btn-sm" onclick="deleteArticle(${articulo.articulo_id})">Eliminar</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
        }
        
        // Cargar categorías (sin cambios)
        if (path.includes("categorias.html")) {
            const categorias = await apiCall('/categorias');
            console.log(categorias)
            const tbody = document.querySelector('#categories-table tbody');
            tbody.innerHTML = '';

            categorias.forEach(categoria => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${categoria.category_name}</td>
                    <td>
                        <a href="articulos_categoria.html?categoria=${encodeURIComponent(categoria.category_name)}" 
                        class="category-link" 
                        title="Ver artículos de esta categoría">
                            ${categoria.url_cat}
                        </a>
                    </td>
                    <td class="action-buttons">
                        <button class="btn btn-primary btn-sm" onclick="editCategory('${categoria.category_name.replace(/'/g, "\\'")}', '${categoria.url_cat.replace(/'/g, "\\'")}')">Editar</button>
                        <button class="btn btn-danger btn-sm" onclick="deleteCategory('${categoria.category_name.replace(/'/g, "\\'")}')">Eliminar</button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }
        
        // Cargar comentarios
        if (path.includes("comentarios.html")) {
            const comentarios = await apiCall('/comentarios');
            const tbody = document.querySelector('#comments-table tbody');
            tbody.innerHTML = '';
            
            comentarios.forEach(comentario => {
                const tr = document.createElement('tr');
                // --- CAMBIO: Se eliminó el botón de Editar ---
                tr.innerHTML = `
                    <td>${comentario._id}</td>
                    <td>${comentario.article_title} (ID: ${comentario.article_id})</td>
                    <td>${comentario.user_name} (ID: ${comentario.user_id})</td>
                    <td>${comentario.comment}</td>
                    <td class="action-buttons">
                        <button class="btn btn-danger btn-sm" onclick="deleteComment(${comentario._id})">Eliminar</button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }
        
        // Cargar tags (sin cambios)
        if (path.includes("tags.html")) {
            const tags = await apiCall('/tags');
            const tbody = document.querySelector('#tags-table tbody');
            tbody.innerHTML = '';
            tags.forEach(tag => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${tag.name}</td>
                    <td>
                        <a href="articulos_tag.html?tag=${encodeURIComponent(tag.name)}" 
                        class="category-link" 
                        title="Ver artículos con este tag">
                            ${tag.url}
                        </a>
                    </td>
                    <td class="action-buttons">
                        <button class="btn btn-primary btn-sm" onclick="editTag('${tag.name.replace(/'/g, "\\'")}', '${tag.url.replace(/'/g, "\\'")}')">Editar</button>
                        <button class="btn btn-danger btn-sm" onclick="deleteTag('${tag.name.replace(/'/g, "\\'")}')">Eliminar</button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }
        
        // Cargar usuarios (sin cambios)
        if (path.includes("usuarios.html")) {
            const usuarios = await apiCall('/usuarios');
            const tbody = document.querySelector('#users-table tbody');
            tbody.innerHTML = '';
            
            usuarios.forEach(usuario => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${usuario.id}</td>
                    <td>${usuario.name}</td>
                    <td>${usuario.email}</td>
                    <td class="action-buttons">
                        <button class="btn btn-primary btn-sm" onclick="editUser('${usuario.email.replace(/'/g, "\\'")}', '${usuario.name.replace(/'/g, "\\'")}', '${usuario.email.replace(/'/g, "\\'")}')">Editar</button>
                        <button class="btn btn-danger btn-sm" onclick="deleteUser('${usuario.email.replace(/'/g, "\\'")}')">Eliminar</button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (error) {
        console.error('Error cargando datos:', error);
    }
}

// --- CAMBIO: Se eliminó la función editArticle ---
async function deleteArticle(id) {
    if (confirm('¿Estás seguro de que deseas eliminar este artículo?')) {
        try {
            await apiCall(`/articulos/${id}`, { method: 'DELETE' });
            showMessage('Artículo eliminado correctamente', 'success');
            loadRealData();
        } catch (error) {
            // El error ya se maneja en apiCall
        }
    }
}

// Funciones para Categorías (sin cambios)
function editCategory(name, url) {
    document.getElementById('original-name').value = name;
    document.getElementById('category-name').value = name;
    document.getElementById('url-cat').value = url;
    document.getElementById('form-title').textContent = 'Editar Categoría';
}

async function deleteCategory(name) {
    if (confirm('¿Estás seguro de que deseas eliminar esta categoría?')) {
        try {
            await apiCall(`/categorias/${encodeURIComponent(name)}`, { method: 'DELETE' });
            showMessage('Categoría eliminada correctamente', 'success');
            loadRealData();
        } catch (error) {}
    }
}

// --- CAMBIO: Se eliminó la función editComment ---
async function deleteComment(id) {
    if (confirm('¿Estás seguro de que deseas eliminar este comentario?')) {
        try {
            await apiCall(`/comentarios/${id}`, { method: 'DELETE' });
            showMessage('Comentario eliminado correctamente', 'success');
            loadRealData();
        } catch (error) {}
    }
}

// Funciones para Tags (sin cambios)
function editTag(name, url) {
    document.getElementById('original-tag-name').value = name;
    document.getElementById('tag-name').value = name;
    document.getElementById('url-tag').value = url;
    document.getElementById('form-title').textContent = 'Editar Tag';
}

async function deleteTag(name) {
    if (confirm('¿Estás seguro de que deseas eliminar este tag?')) {
        try {
            await apiCall(`/tags/${encodeURIComponent(name)}`, { method: 'DELETE' });
            showMessage('Tag eliminado correctamente', 'success');
            loadRealData();
        } catch (error) {}
    }
}

// Funciones para Usuarios (sin cambios)
function editUser(email, name, newEmail) {
    document.getElementById('original-email').value = email;
    document.getElementById('user-name').value = name;
    document.getElementById('user-email').value = newEmail;
    document.getElementById('form-title').textContent = 'Editar Usuario';
    document.getElementById('update-name').checked = true;
    document.getElementById('update-email').checked = true;
}

async function deleteUser(email) {
    if (confirm('¿Estás seguro de que deseas eliminar este usuario?')) {
        try {
            await apiCall(`/usuarios/${encodeURIComponent(email)}`, { method: 'DELETE' });
            showMessage('Usuario eliminado correctamente', 'success');
            loadRealData();
        } catch (error) {}
    }
}

// Configuración de formularios
document.addEventListener('DOMContentLoaded', function() {
    loadRealData();
    const tagsContainer = document.getElementById('tags-container');
    const categoriesContainer = document.getElementById('categories-container');

    if (tagsContainer && categoriesContainer) {
        loadTags();
        loadCategorias();
    }
    
    const cancelButtons = document.querySelectorAll('#cancel-edit');
    cancelButtons.forEach(button => {
        button.addEventListener('click', function() {
            const form = this.closest('form');
            form.reset();
            const formTitle = document.getElementById('form-title');
            if (formTitle) {
                formTitle.textContent = formTitle.textContent.replace('Editar', 'Agregar Nuevo');
            }
        });
    });
    
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formTitle = document.getElementById('form-title');
            const isEdit = formTitle && formTitle.textContent.includes('Editar');
            
            try {
                if (form.id === 'article-form') {
                    
                    const data = {
                        user_id: 0, // ID de Admin
                        titulo: document.getElementById('titulo').value,
                        article_text: document.getElementById('article-text').value,
                        tags: Array.from(selectedTags),
                        categories: Array.from(selectedCategories)
                    };
                    
                    // La lógica de 'isEdit' ya no es necesaria aquí, pero la dejamos por si se reactiva en el futuro
                    if (isEdit) {
                        // Esta parte ya no se usará
                    } else {
                        await apiCall('/articulos', {
                            method: 'POST',
                            body: JSON.stringify(data)
                        });
                    }
                }
                else if (form.id === 'category-form') {
                    // Lógica para categorías sin cambios
                    const data = {
                        category_name: document.getElementById('category-name').value,
                        url_cat: document.getElementById('url-cat').value
                    };
                    if (isEdit) {
                        const originalName = document.getElementById('original-name').value;
                        await apiCall(`/categorias/${encodeURIComponent(originalName)}`, {
                            method: 'PUT',
                            body: JSON.stringify({ category_name: data.category_name, url_cat: data.url_cat})
                        });
                    } else {
                        await apiCall('/categorias', { method: 'POST', body: JSON.stringify(data) });
                    }
                }
                else if (form.id === 'comment-form') {
                    // --- CAMBIO: user_id se establece a 0 en la inserción ---
                    const data = {
                        articulo_id: parseInt(document.getElementById('article-id-comment').value),
                        user_id: 0, // ID de Admin
                        texto_com: document.getElementById('texto-com').value
                    };
                    
                    if (isEdit) {
                        // Esta parte ya no se usará
                    } else {
                        await apiCall('/comentarios', {
                            method: 'POST',
                            body: JSON.stringify(data)
                        });
                    }
                }
                else if (form.id === 'tag-form') {
                    // Lógica para tags sin cambios
                    const data = {
                        name: document.getElementById('tag-name').value,
                        url: document.getElementById('url-tag').value
                    };
                    console.log(data)
                    if (isEdit) {
                        const originalName = document.getElementById('original-tag-name').value;
                        await apiCall(`/tags/${encodeURIComponent(originalName)}`, {
                            method: 'PUT',
                            body: JSON.stringify({ name: data.name, url: data.url })
                        });
                    } else {
                        await apiCall('/tags', { method: 'POST', body: JSON.stringify(data) });
                    }
                }
                else if (form.id === 'user-form') {
                    // Lógica para usuarios sin cambios
                    const data = {
                        user_name: document.getElementById('user-name').value,
                        email: document.getElementById('user-email').value
                    };
                    if (isEdit) {
                        data.name_bool = document.getElementById('update-name').checked ? 1 : 0;
                        data.email_bool = document.getElementById('update-email').checked ? 1 : 0;
                        const originalEmail = document.getElementById('original-email').value;
                        await apiCall(`/usuarios/${encodeURIComponent(originalEmail)}`, {
                            method: 'PUT',
                            body: JSON.stringify(data)
                        });
                    } else {
                        await apiCall('/usuarios', { method: 'POST', body: JSON.stringify(data) });
                    }
                }
                
                showMessage(isEdit ? 'Registro actualizado correctamente' : 'Registro creado correctamente', 'success');
                this.reset();
                if (formTitle) {
                    formTitle.textContent = formTitle.textContent.replace('Editar', 'Agregar Nuevo');
                }
                loadRealData();

                
            } catch (error) {
                // El error ya se maneja en apiCall
            }
        });
    });
});
