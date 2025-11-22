// Configuración de la API
const API_BASE_URL = 'http://localhost:5000/api';

// Función para obtener parámetros de la URL
function getQueryParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

// Función para mostrar mensajes (similar a la del script principal)
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

// Función para cargar artículos por tag
async function loadArticulosPorTag() {
    const tag = getQueryParam('tag');
    
    if (!tag) {
        showMessage('No se especificó un tag', 'error');
        return;
    }
    
    // Actualizar título
    document.getElementById('titulo-tag').textContent = `Artículos del tag: ${tag}`;
    
    try {  
        const response = await fetch(`${API_BASE_URL}/tag/${encodeURIComponent(tag)}/articulos`);
        if (!response.ok) {
            throw new Error('Error al cargar los artículos');
        }
        
        const data = await response.json();
        
        // Ocultar mensaje de carga
        document.getElementById('loading-message').style.display = 'none';
        
        if (data.count === 0) {
            // Mostrar mensaje de no hay artículos
            document.getElementById('no-articles-message').style.display = 'block';
            return;
        }
        
        // Mostrar contenedor de artículos
        const container = document.getElementById('articles-container');
        container.style.display = 'block';

        // Generar HTML para los artículos
        container.innerHTML = data.articulos.map(articulo => `
            <div class="article-card">
                <div class="article-header">
                    <h3 class="article-title">${articulo.title}</h3>
                    <span class="article-date">${new Date(articulo.created_at.$date).toLocaleDateString('es-ES')}</span>
                </div>
                <div class="article-author">
                    <strong>Autor:</strong> ${articulo.author_name}
                </div>
                <div class="article-excerpt">
                    ${articulo.excerpt}
                </div>
                <div class="article-meta">
                    <div class="article-tags">
                        <strong>Tags:</strong> ${articulo.tags.map(t => 
                            t === tag ? `<span class="tag tag-highlight">${t}</span>` : `<span class="tag">${t}</span>`
                        ).join('')}
                    </div>
                    <div class="article-categories">
                        <strong>Categorías:</strong> ${articulo.categories.map(cat => `<span class="category">${cat}</span>`).join('')}
                    </div>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error cargando artículos:', error);
        document.getElementById('loading-message').style.display = 'none';
        document.getElementById('no-articles-message').style.display = 'block';
        showMessage('Error al cargar los artículos: ' + error.message, 'error');
    }
}

// Cargar artículos cuando la página esté lista
document.addEventListener('DOMContentLoaded', loadArticulosPorTag);