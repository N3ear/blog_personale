function showProfileMessage(text, type = "error") {
    const el = document.getElementById("profile-message");
    if (!el) return;
    el.textContent = text;
    el.className = `message ${type}`;
}

document.addEventListener("DOMContentLoaded", async () => {
    const token = localStorage.getItem("token");

    // Se non c'e token -> vai al login
    if (!token) {
        window.location.href = "/login";
        return;
    }

    const usernameEl = document.getElementById("username");
    const emailEl = document.getElementById("email");
    const isAdminEl = document.getElementById("is_admin");
    const form = document.getElementById("profile-edit-form");
    const editBtn = document.getElementById("profile-edit-btn");

    try {
        const meRes = await fetch("/api/me", {
            method: "GET",
            headers: { "Authorization": "Bearer " + token }
        });

        const me = await meRes.json();
        if (!meRes.ok) {
            showProfileMessage(me.error || "Errore nel caricamento del profilo");
            return;
        }

        if (usernameEl) usernameEl.textContent = me.username || "";
        if (emailEl) emailEl.textContent = me.email || "";
        if (isAdminEl) isAdminEl.textContent = me.is_admin ? "Si" : "No";

        if (form && editBtn) {
            const pageUsername = form.dataset.username;
            const canEdit = me.username === pageUsername || me.is_admin;

            if (canEdit) {
                editBtn.style.display = "inline-block";

                editBtn.addEventListener("click", () => {
                    form.style.display = form.style.display === "grid" ? "none" : "grid";
                });

                form.addEventListener("submit", async (e) => {
                    e.preventDefault();
                    const formData = new FormData(form);

                    const res = await fetch(`/api/profile/${pageUsername}`, {
                        method: "POST",
                        headers: { "Authorization": "Bearer " + token },
                        body: formData
                    });

                    const data = await res.json();
                    if (!res.ok) {
                        showProfileMessage(data.error || "Errore aggiornamento profilo");
                        return;
                    }

                    showProfileMessage("Profilo aggiornato con successo.", "success");
                    setTimeout(() => window.location.reload(), 600);
                });
            }
        }
    } catch (err) {
        showProfileMessage("Errore di rete. Controlla la connessione e riprova.");
    }
});
