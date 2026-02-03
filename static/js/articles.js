// ==========================
// INFO UTENTE LOGGATO
// ==========================
async function loadUser() {
    const res = await fetch("/api/me");

    const userBar = document.getElementById("user-bar");

    if (res.status === 401) {
        userBar.innerHTML = `
            <p>Non sei loggato.
            <a href="/login">Login</a></p>
        `;
        return;
    }

    const user = await res.json();

    userBar.innerHTML = `
        <p>Ciao <strong>${user.username}</strong></p>
        <button onclick="logout()">Logout</button>
    `;
}

// ==========================
// LOGOUT
// ==========================
async function logout() {
    const res = await fetch("/api/logout", {
        method: "POST"
    });

    if (res.ok) {
        window.location.href = "/login";
    } else {
        alert("Errore nel logout");
    }
}


// ==========================
// CARICA ARTICOLI
// ==========================
console.log("ARTICLES JS CARICATO")

function showMessage(text, type = "error") {
    const el = document.getElementById("message");
    if (!el) return;
    el.textContent = text;
    el.className = `message ${type}`;
}

let currentUser = null;

async function loadCurrentUser() {
    try {
        const res = await fetch("/api/me");
        if (!res.ok) {
            currentUser = null;
            return;
        }
        currentUser = await res.json();
    } catch (err) {
        currentUser = null;
    }
}

async function loadArticles() {
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
            div.classList.add("article");

            const canManageArticle = currentUser
                && (currentUser.is_admin || currentUser.id === article.author_id);

            div.innerHTML = `
                <h2>${article.title}</h2>
                <p>${article.content}</p>
                <small>Autore: ${article.author}</small>
                ${canManageArticle ? `
                    <button onclick="toggleEditArticle(${article.id})">Modifica articolo</button>
                    <button onclick="deleteArticle(${article.id})">Elimina articolo</button>
                ` : ""}
                <div id="edit-article-${article.id}" style="display:none; margin-top: 8px;">
                    <input type="text" id="edit-title-${article.id}" value="${article.title}">
                    <textarea id="edit-content-${article.id}" rows="4">${article.content}</textarea>
                    <button onclick="saveArticle(${article.id})">Salva</button>
                    <button onclick="toggleEditArticle(${article.id})">Annulla</button>
                </div>

                <h4>Commenti</h4>
                <div id="comments-${article.id}">
                    <p>Caricamento commenti...</p>
                </div>

                <input type="text" id="comment-${article.id}" placeholder="Scrivi un commento">
                <button onclick="addComment(${article.id})">Invia</button>

                <hr>
            `;

            container.appendChild(div);

            loadComments(article.id);
        });
    } catch (err) {
        showMessage("Errore di rete nel caricamento degli articoli.");
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

            const canManageComment = currentUser
                && (currentUser.is_admin || currentUser.id === c.author_id);

            div.innerHTML = `
                <p><strong>${c.author}</strong>: ${c.content}</p>
                <small>${c.date_posted}</small>
                ${canManageComment ? `
                    <button onclick="toggleEditComment(${c.id})">Modifica commento</button>
                    <button onclick="deleteComment(${c.id}, ${articleId})">Elimina commento</button>
                ` : ""}
                <div id="edit-comment-${c.id}" style="display:none; margin-top: 6px;">
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
// CREA ARTICOLO
// ==========================
async function createArticle() {
    const title = document.getElementById("title").value;
    const content = document.getElementById("content").value;

    const res = await fetch("/api/articles", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ title, content })
    });

    if (res.ok) {
        document.getElementById("title").value = "";
        document.getElementById("content").value = "";
        loadArticles();
        showMessage("Articolo creato con successo.", "success");
    } else {
        showMessage("Errore nella creazione dell'articolo. Controlla i campi.");
    }
}

// ==========================
// AGGIUNGI COMMENTO
// ==========================
async function addComment(articleId) {
    const input = document.getElementById(`comment-${articleId}`);
    const content = input.value;

    if (!content) {
        showMessage("Scrivi un commento prima di inviare.");
        return;
    }

    const res = await fetch(`/api/articles/${articleId}/comments`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ content })
    });

    if (res.ok) {
        input.value = "";
        loadComments(articleId);
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
    const title = document.getElementById(`edit-title-${articleId}`).value;
    const content = document.getElementById(`edit-content-${articleId}`).value;

    const res = await fetch(`/api/articles/${articleId}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ title, content })
    });

    if (res.ok) {
        loadArticles();
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
    const content = document.getElementById(`edit-comment-content-${commentId}`).value;

    const res = await fetch(`/api/comments/${commentId}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json"
        },
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
    if (!confirmed) {
        return;
    }

    const res = await fetch(`/api/articles/${articleId}`, {
        method: "DELETE"
    });

    if (res.ok) {
        loadArticles();
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
    if (!confirmed) {
        return;
    }

    const res = await fetch(`/api/comments/${commentId}`, {
        method: "DELETE"
    });

    if (res.ok) {
        loadComments(articleId);
        showMessage("Commento eliminato.", "success");
    } else {
        showMessage("Errore nell'eliminazione del commento. Riprova.");
    }
}

// AVVIO
loadArticles();
loadUser();
loadArticles();
