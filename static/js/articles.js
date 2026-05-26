// ==========================
// INFO UTENTE LOGGATO
// ==========================
function getToken() {
    return localStorage.getItem("token");
}

function getAuthHeaders(extra = {}) {
    const token = getToken();
    const headers = { ...extra };
    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }
    return headers;
}

async function authFetch(url, options = {}) {
    const opts = { ...options };
    opts.headers = getAuthHeaders(options.headers || {});
    const res = await fetch(url, opts);
    if (res.status === 401) {
        localStorage.removeItem("token");
        window.location.href = "/login";
    }
    return res;
}

async function loadUser() {
    const res = await authFetch("/api/me");
    const userBar = document.getElementById("user-bar");
    const profileLinkContainer = document.getElementById("profile-link-container");
    if (res.status === 401) {
        userBar.innerHTML = `
            <p>Non sei loggato.
                <a href="/login">Login</a>
            </p>
        `;
        if (profileLinkContainer) {
            profileLinkContainer.innerHTML = "";
        }
        return;
    }
    const user = await res.json();
    userBar.innerHTML = `
        <p>Ciao <strong>${user.username}</strong></p>
        <button onclick="logout()">Logout</button>
    `;
    if (profileLinkContainer) {
        profileLinkContainer.innerHTML = `<a class="profile-link-btn" href="/profile/${user.username}">Vai al mio profilo</a>`;
    }
}

// ==========================
// LOGOUT
// ==========================
async function logout() {
    const res = await authFetch("/api/logout", { method: "POST" });
    if (res.ok) {
        localStorage.removeItem("token");
        window.location.href = "/login";
    } else {
        alert("Errore nel logout");
    }
}

// ==========================
// UI HELPERS
// ==========================
// ==========================
// TOAST NOTIFICATIONS
// ==========================
function showToast(message, type = 'success') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.className = `toast ${type === 'error' ? 'error' : ''}`;
    toast.innerText = message;

    container.appendChild(toast);

    // Rimuovi il toast dopo 3 secondi
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 500);
    }, 3000);
}

function showMessage(text, type = "error") {
    // Reindirizziamo a showToast per un'esperienza più moderna
    showToast(text, type);
}

let currentUser = null;
let categories = [];
let isLoading = false;

async function loadCurrentUser() {
    try {
        const res = await authFetch("/api/me");
        if (!res.ok) {
            currentUser = null;
            return;
        }
        currentUser = await res.json();
    } catch (err) {
        currentUser = null;
    }
}

// ==========================
// CARICA ARTICOLI
// ==========================
async function loadArticles() {
    if (isLoading) return;
    isLoading = true;
    try {
        await loadCurrentUser();
        const res = await fetch("/api/articles");
        if (!res.ok) {
            showMessage("Errore nel caricamento degli articoli. Riprova.");
            return;
        }
        const articles = await res.json();
        const container = document.getElementById("articles-container");
        container.innerHTML = "";
        if (articles.length === 0) {
            container.innerHTML = "<p>Nessun articolo presente</p>";
            return;
        }
        articles.forEach(article => {
            const div = document.createElement("div");
            div.classList.add("article", "card");
            const canManageArticle = currentUser && (currentUser.is_admin || currentUser.id === article.author_id);
            div.innerHTML = `
                <h2 class="titolo-articolo">${article.title}</h2>
                ${article.image ? `<img src="/static/uploads/${article.image}" alt="Immagine articolo" style="max-width:100%;display:block;border-radius:10px;margin:8px 0;"/>` : ""}
                <p>${article.content}</p>
                <small>Autore: ${article.author}</small>
                <div class="meta-line">
                    <span class="badge">Like: <span id="like-count-${article.id}">${article.likes}</span></span>
                    ${article.category ? `<span class="badge category-badge" data-category="${article.category.toLowerCase()}">Categoria: ${article.category}</span>` : ""}
                </div>
                <div class="like-row">
                    <button onclick="addLike(${article.id})" aria-label="Mi piace">👍</button>
                    <button onclick="removeLike(${article.id})" aria-label="Non mi piace">👎</button>
                </div>
                ${canManageArticle ? `
                    <button onclick="toggleEditArticle(${article.id})">Modifica articolo</button>
                    <button onclick="deleteArticle(${article.id})">Elimina articolo</button>
                ` : ""}
                <div id="edit-article-${article.id}" style="display:none;margin-top:8px;">
                    <input type="text" id="edit-title-${article.id}" value="${article.title}">
                    <textarea id="edit-content-${article.id}" rows="4">${article.content}</textarea>
                    ${renderCategorySelect(`edit-category-${article.id}`, article.category_id)}
                    <input type="text" id="edit-category-name-${article.id}" placeholder="Oppure scrivi nuova categoria">
                    <button onclick="saveArticle(${article.id})">Salva</button>
                    <button onclick="toggleEditArticle(${article.id})">Annulla</button>
                </div>
                <h4>Commenti</h4>
                <div id="comments-${article.id}"><p>Caricamento commenti...</p></div>
                <input type="text" id="comment-${article.id}" placeholder="Scrivi un commento">
                <button onclick="addComment(${article.id})">Invia</button>
                <hr>
            `;
            container.appendChild(div);
            loadComments(article.id);
        });
    } catch (err) {
        showMessage("Errore di rete nel caricamento degli articoli.");
    } finally {
        isLoading = false;
    }
}

// ==========================
// CARICA COMMENTI
// ==========================
async function loadComments(articleId) {
    try {
        const res = await fetch(`/api/articles/${articleId}/comments`);
        if (!res.ok) {
            showMessage("Errore nel caricamento dei commenti.");
            return;
        }
        const comments = await res.json();
        const container = document.getElementById(`comments-${articleId}`);
        container.innerHTML = "";
        if (comments.length === 0) {
            container.innerHTML = "<p>Nessun commento</p>";
            return;
        }
        comments.forEach(c => {
            const div = document.createElement("div");
            div.classList.add("comment");
            const canManageComment = currentUser && (currentUser.is_admin || currentUser.id === c.author_id);
            div.innerHTML = `
                <p><strong>${c.author}</strong>: ${c.content}</p>
                <small>${c.date_posted}</small>
                ${canManageComment ? `
                    <button onclick="toggleEditComment(${c.id})">Modifica commento</button>
                    <button onclick="deleteComment(${c.id}, ${articleId})">Elimina commento</button>
                ` : ""}
                <div id="edit-comment-${c.id}" style="display:none;margin-top:6px;">
                    <input type="text" id="edit-comment-content-${c.id}" value="${c.content}">
                    <button onclick="saveComment(${c.id}, ${articleId})">Salva</button>
                    <button onclick="toggleEditComment(${c.id})">Annulla</button>
                </div>
            `;
            container.appendChild(div);
        });
    } catch (err) {
        showMessage("Errore di rete nel caricamento dei commenti.");
    }
}

// ==========================
// CREA ARTICOLO (FORMDATA)
// ==========================
async function createArticle() {
    const title = document.getElementById("title").value.trim();
    const content = document.getElementById("content").value.trim();
    const categoryId = document.getElementById("category-select")?.value;
    const categoryName = document.getElementById("category-name")?.value.trim();
    const imageFile = document.getElementById("image")?.files[0];

    if (!title || !content) {
        showMessage("Titolo e contenuto sono obbligatori.");
        return;
    }

    const formData = new FormData();
    formData.append("title", title);
    formData.append("content", content);
    
    if (categoryName) {
        formData.append("category_name", categoryName);
    } else if (categoryId) {
        formData.append("category_id", categoryId);
    }
    
    if (imageFile) {
        formData.append("image", imageFile);
    }

    const res = await authFetch("/api/articles", {
        method: "POST",
        headers: getAuthHeaders(), // Content-Type is automatically set by fetch when body is FormData
        body: formData
    });
    
    let data;
    try {
        data = await res.json();
    } catch (e) {
        data = { error: "Errore di parsing JSON" };
    }
    
    if (!res.ok) {
        const errMsg = data.error ? (typeof data.error === 'object' ? JSON.stringify(data.error) : data.error) : "Errore nella creazione dell'articolo";
        showMessage(errMsg);
        return;
    }
    // clear form fields
    document.getElementById("title").value = "";
    document.getElementById("content").value = "";
    const catSelect = document.getElementById("category-select");
    if (catSelect) catSelect.value = "";
    const catName = document.getElementById("category-name");
    if (catName) catName.value = "";
    const imageInput = document.getElementById("image");
    if (imageInput) imageInput.value = "";
    
    await loadCategories();
    await loadArticles();
    caricaStatistiche();
    showMessage("Articolo creato con successo.", "success");
}

// ==========================
// AGGIUNGI COMMENTO
// ==========================
async function addComment(articleId) {
    const input = document.getElementById(`comment-${articleId}`);
    const content = input.value.trim();
    if (!content) {
        showMessage("Scrivi un commento prima di inviare.");
        return;
    }
    const res = await authFetch(`/api/articles/${articleId}/comments`, {
        method: "POST",
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({ content })
    });
    if (res.ok) {
        input.value = "";
        loadComments(articleId);
        caricaStatistiche();
        showMessage("Commento inviato.", "success");
    } else {
        showMessage("Errore nell'invio del commento. Riprova.");
    }
}

// ==========================
// MODIFICA ARTICOLO
// ==========================
function toggleEditArticle(articleId) {
    const box = document.getElementById(`edit-article-${articleId}`);
    if (!box) return;
    box.style.display = box.style.display === "none" ? "block" : "none";
}

async function saveArticle(articleId) {
    const title = document.getElementById(`edit-title-${articleId}`).value.trim();
    const content = document.getElementById(`edit-content-${articleId}`).value.trim();
    const categoryId = document.getElementById(`edit-category-${articleId}`)?.value;
    const categoryName = document.getElementById(`edit-category-name-${articleId}`).value.trim();
    const res = await authFetch(`/api/articles/${articleId}`, {
        method: "PUT",
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({
            title,
            content,
            category_id: categoryId ? Number(categoryId) : null,
            category_name: categoryName || undefined
        })
    });
    if (res.ok) {
        await loadCategories();
        await loadArticles();
        showMessage("Articolo aggiornato.", "success");
    } else {
        showMessage("Errore nella modifica dell'articolo. Riprova.");
    }
}

// ==========================
// MODIFICA COMMENTO
// ==========================
function toggleEditComment(commentId) {
    const box = document.getElementById(`edit-comment-${commentId}`);
    if (!box) return;
    box.style.display = box.style.display === "none" ? "block" : "none";
}

async function saveComment(commentId, articleId) {
    const content = document.getElementById(`edit-comment-content-${commentId}`).value.trim();
    const res = await authFetch(`/api/comments/${commentId}`, {
        method: "PUT",
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({ content })
    });
    if (res.ok) {
        loadComments(articleId);
        showMessage("Commento aggiornato.", "success");
    } else {
        showMessage("Errore nella modifica del commento. Riprova.");
    }
}

// ==========================
// ELIMINA ARTICOLO
// ==========================
async function deleteArticle(articleId) {
    const confirmed = confirm("Sei sicuro di voler eliminare questo articolo?");
    if (!confirmed) return;
    const res = await authFetch(`/api/articles/${articleId}`, { method: "DELETE" });
    if (res.ok) {
        loadArticles();
        caricaStatistiche();
        showMessage("Articolo eliminato.", "success");
    } else {
        showMessage("Errore nell'eliminazione dell'articolo. Riprova.");
    }
}

// ==========================
// ELIMINA COMMENTO
// ==========================
async function deleteComment(commentId, articleId) {
    const confirmed = confirm("Sei sicuro di voler eliminare questo commento?");
    if (!confirmed) return;
    const res = await authFetch(`/api/comments/${commentId}`, { method: "DELETE" });
    if (res.ok) {
        loadComments(articleId);
        caricaStatistiche();
        showMessage("Commento eliminato.", "success");
    } else {
        showMessage("Errore nell'eliminazione del commento. Riprova.");
    }
}

// ==========================
// CATEGORIE
// ==========================
function renderCategorySelect(elementId, selectedId = null) {
    const options = ['<option value="">Senza categoria</option>']
        .concat(categories.map(c => `<option value="${c.id}" ${selectedId === c.id ? "selected" : ""}>${c.name}</option>`));
    return `<select id="${elementId}" class="select-cat">${options.join("")}</select>`;
}

async function loadCategories() {
    try {
        const res = await fetch("/api/categories");
        if (!res.ok) return;
        categories = await res.json();
        
        // Aggiorna il select della creazione
        const select = document.getElementById("category-select");
        if (select) {
            select.innerHTML = renderCategorySelect("category-select").replace(/^<select[^>]*>|<\/select>$/g, "");
        }
        
        // Aggiorna i filtri in alto
        renderCategoryFilters();
    } catch (e) {
        console.error("Errore caricamento categorie", e);
    }
}

// ==========================
// LIKE
// ==========================
async function addLike(articleId) {
    if (!getToken()) {
        window.location.href = "/login";
        return;
    }
    const res = await authFetch(`/api/articles/${articleId}/likes`, { method: "POST" });
    await refreshLikes(articleId, res.ok);
}

async function removeLike(articleId) {
    if (!getToken()) {
        window.location.href = "/login";
        return;
    }
    const res = await authFetch(`/api/articles/${articleId}/likes`, { method: "DELETE" });
    await refreshLikes(articleId, res.ok);
}

async function refreshLikes(articleId, success) {
    if (!success) {
        showMessage("Errore nel mettere/togliere like.");
        return;
    }
    const countRes = await fetch(`/api/articles/${articleId}/likes`);
    if (countRes.ok) {
        const data = await countRes.json();
        const el = document.getElementById(`like-count-${articleId}`);
        if (el) el.textContent = data.likes;
        caricaStatistiche();
    } else {
        loadArticles();
    }
}

// ==========================
// FILTRO CATEGORIE
// ==========================
function renderCategoryFilters() {
    const container = document.getElementById("category-filters");
    if (!container) return;

    let html = `<button class="pill-button active" data-cat="" onclick="filterByCategory('')">Tutte</button>`;
    categories.forEach(cat => {
        html += `<button class="pill-button" data-cat="${cat.name.toLowerCase()}" onclick="filterByCategory('${cat.name.toLowerCase()}')">${cat.name}</button>`;
    });
    container.innerHTML = html;
}

function toggleCategorySection() {
    const section = document.getElementById("category-filters");
    if (!section) return;
    section.style.display = (section.style.display === "none" || section.style.display === "") ? "flex" : "none";
}

function filterByCategory(categoryName) {
    // Aggiorna lo stato visivo dei bottoni
    document.querySelectorAll("#category-filters .pill-button").forEach(btn => {
        if (btn.getAttribute("data-cat") === categoryName) {
            btn.classList.add("active");
        } else {
            btn.classList.remove("active");
        }
    });

    filtraArticoli(categoryName, true);
    // Richiudi la sezione dopo la scelta
    toggleCategorySection();
}

// ==========================
// STATISTICHE
// ==========================
async function caricaStatistiche() {
    try {
        const res = await fetch("/api/stats");
        if (!res.ok) return;
        const data = await res.json();
        
        document.getElementById("stat-articles").textContent = data.articles;
        document.getElementById("stat-comments").textContent = data.comments;
        document.getElementById("stat-likes").textContent = data.likes;
    } catch (err) {
        console.error("Errore caricamento statistiche", err);
    }
}

async function init() {
    await loadCategories();
    await loadArticles();
    await loadUser();
    await caricaStatistiche();
}

// ==========================
// RICERCA ARTICOLI
// ==========================
function filtraArticoli(filterValue = "", isCategory = false) {
    let input = filterValue.toLowerCase().trim();
    
    let cards = document.querySelectorAll('#articles-container .article');

    cards.forEach(card => {
        // Se non c'è filtro, mostra tutto
        if (!input) {
            card.style.setProperty('display', 'block', 'important');
            return;
        }

        if (isCategory) {
            // Filtro STRETTO per categoria
            const catBadge = card.querySelector('.category-badge');
            const articleCat = catBadge ? catBadge.getAttribute('data-category') : "";
            
            if (articleCat === input) {
                card.style.setProperty('display', 'block', 'important');
            } else {
                card.style.setProperty('display', 'none', 'important');
            }
        } else {
            // Ricerca testuale generica
            let keywords = input.split(/\s+/).filter(k => k.length > 0);
            let titolo = card.querySelector('h2')?.innerText.toLowerCase() || "";
            let contenuto = card.querySelector('p')?.innerText.toLowerCase() || "";
            let badges = Array.from(card.querySelectorAll('.badge')).map(b => b.innerText.toLowerCase()).join(" ");
            
            let testoCard = (titolo + " " + contenuto + " " + badges).trim();
            let matches = keywords.every(kw => testoCard.includes(kw));

            if (matches) {
                card.style.setProperty('display', 'block', 'important');
            } else {
                card.style.setProperty('display', 'none', 'important');
            }
        }
    });
}

init();
