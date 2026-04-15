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
    const passwordForm = document.getElementById("password-edit-form");
    const passwordBtn = document.getElementById("password-edit-btn");

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
                if (passwordBtn) {
                    passwordBtn.style.display = "inline-block";
                }

                editBtn.addEventListener("click", () => {
                    form.style.display = form.style.display === "grid" ? "none" : "grid";
                });
                if (passwordBtn && passwordForm) {
                    passwordBtn.addEventListener("click", () => {
                        passwordForm.style.display = passwordForm.style.display === "grid" ? "none" : "grid";
                    });
                }

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

        if (passwordForm) {
            passwordForm.addEventListener("submit", async (e) => {
                e.preventDefault();
                const currentPassword = passwordForm.querySelector("input[name='current_password']").value;
                const newPassword = passwordForm.querySelector("input[name='new_password']").value;

                if (!currentPassword || !newPassword) {
                    showProfileMessage("Inserisci entrambe le password.");
                    return;
                }

                const res = await fetch("/api/change-password", {
                    method: "POST",
                    headers: {
                        "Authorization": "Bearer " + token,
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        current_password: currentPassword,
                        new_password: newPassword
                    })
                });

                const data = await res.json();
                if (!res.ok) {
                    showProfileMessage(data.error || "Errore cambio password");
                    return;
                }

                showProfileMessage("Password aggiornata con successo.", "success");
                passwordForm.reset();
                passwordForm.style.display = "none";
            });
        }
    } catch (err) {
        showProfileMessage("Errore di rete. Controlla la connessione e riprova.");
    }
});
