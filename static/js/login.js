function showMessage(text, type = "error") {
    const el = document.getElementById("message");
    if (!el) return;
    el.textContent = text;
    el.className = `message ${type}`;
}

document.getElementById("loginForm").addEventListener("submit", async function (e) {
    e.preventDefault();

    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    try {
        const res = await fetch("/api/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password }),
            credentials: "include"
        });

        let data = null;
        try {
            data = await res.json();
        } catch (err) {
            data = null;
        }

        if (!data) {
            alert("Errore di rete. Controlla la connessione e riprova.");
            return;
        }

        // 👉 Caso 1: utente inesistente → vai alla pagina di registrazione
        if (data.error === "utente inesistente") {
            alert("Questo utente non esiste. Registrati per creare un nuovo account.");
            window.location.href = "/register";
            return;
        }

        // 👉 Caso 2: password errata
        if (data.error === "password errata") {
            alert("Password errata");
            return;
        }

        // 👉 Caso 3: login corretto
        if (data.message === "Login effettuato") {
            if (data.token) {
                localStorage.setItem("token", data.token);
            }
            window.location.href = "/articles";
        }
    } catch (err) {
        alert("Errore di rete. Controlla la connessione e riprova.");
    }
});

