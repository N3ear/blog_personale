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

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 500);
    }, 3000);
}

function showMessage(text, type = "error") {
    showToast(text, type);
}

document.getElementById("registerForm").addEventListener("submit", async function (e) {
    e.preventDefault();

    const username = document.getElementById("username").value;
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const profile_name = username.trim();

    try {
        const response = await fetch("/api/register", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ username, email, password, profile_name })
        });

        const data = await response.json();

        if (response.ok) {
            showMessage("Registrazione completata. Ora puoi fare login.", "success");
            setTimeout(() => {
                window.location.href = "/login";
            }, 800);
        } else {
            const errorText = data.error || "Errore nella registrazione. Riprova.";
            showMessage(errorText);
            if (errorText.toLowerCase().includes("esist")) {
                setTimeout(() => {
                    window.location.href = "/login";
                }, 900);
            }
        }
    } catch (err) {
        showMessage("Errore di rete. Controlla la connessione e riprova.");
    }
});
