// ----------------------------
// ENVOI D’UN NOUVEAU MESSAGE
// ----------------------------
function sendMessage() {
    let message = document.getElementById("message").value;
    if (message.trim() === "") return;

    let chatBox = document.getElementById("chat-box");

    // Affichage du message utilisateur
    chatBox.innerHTML += `
        <div class="message user">
            <span class="indicator">Vous :</span>
            <div class="text">${message}</div>
        </div>
    `;
    chatBox.scrollTop = chatBox.scrollHeight;

    // Envoi du message au serveur Flask
    fetch("/ask", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: "message=" + encodeURIComponent(message)
    })
    .then(response => response.json())
    .then(data => {

        // Affichage de la réponse du bot
        chatBox.innerHTML += `
            <div class="message bot">
                <span class="indicator">Chatbot :</span>
                <div class="text">${data.reply}</div>
            </div>
        `;
        chatBox.scrollTop = chatBox.scrollHeight;
    });

    // Effacer le champ de saisie
    document.getElementById("message").value = "";
}



// ----------------------------
// FONCTION D'AJOUT POUR L’HISTORIQUE
// ----------------------------
function ajouterMessage(texte, type) {
    const chatBox = document.getElementById("chat-box");

    chatBox.innerHTML += `
        <div class="message ${type}">
            <span class="indicator">${type === "user" ? "Vous :" : "Chatbot :"}</span>
            <div class="text">${texte}</div>
        </div>
    `;

    chatBox.scrollTop = chatBox.scrollHeight;
}



// ----------------------------
// CHARGEMENT DE L’HISTORIQUE
// ----------------------------
async function chargerHistorique() {
    const femme_id = localStorage.getItem("femme_id");

    if (!femme_id) {
        console.error("Aucun femme_id trouvé dans localStorage !");
        return;
    }

    const response = await fetch(`/historique/${femme_id}`);
    const data = await response.json();

    if (data.status === "success") {
        const messages = data.historique;

        // Charger d'abord les anciens messages
        messages.forEach(msg => {
            ajouterMessage(msg.question, "user");
            ajouterMessage(msg.reponse, "bot");
        });
    }
}



// ----------------------------
// LANCER L’HISTORIQUE AU CHARGEMENT
// ----------------------------
window.onload = function() {
    // Message d’accueil automatique
    ajouterMessage(
        "Bonsoir 👋 je suis votre sage-femme virtuelle. Qu'est-ce que vous souhaiteriez savoir sur votre grossesse ou votre bébé aujourd'hui ?",
        "bot"
    );
    chargerHistorique();
}

function viderHistorique() {
    if (!confirm("Voulez-vous vraiment supprimer tout l'historique ?")) return;

    fetch("/historique/supprimer", {
        method: "POST"
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "success") {
            document.getElementById("chat-box").innerHTML = "";
            alert("Historique effacé !");
        } else {
            alert("Erreur : " + data.message);
        }
    });
}


// function sendMessage() {
//     let message = document.getElementById("message").value;
//     if (message.trim() === "") return;

//     // Afficher le message utilisateur avec l'indicateur
//     let chatBox = document.getElementById("chat-box");
//     chatBox.innerHTML += `
//         <div class="message user">
//             <span class="indicator">Vous : </span>
//             <div class="text">${message}</div>
//         </div>`;
//     chatBox.scrollTop = chatBox.scrollHeight;

//     // Envoyer au serveur Flask
//     fetch("/ask", {
//         method: "POST",
//         headers: { "Content-Type": "application/x-www-form-urlencoded" },
//         body: "message=" + encodeURIComponent(message)
//     })
//     .then(response => response.json())
//     .then(data => {
//         // Afficher la réponse du bot avec l'indicateur et l'image
//         chatBox.innerHTML += `
//             <div class="message bot">
//                 <span class="indicator">Chatbot : </span>
//                 <div class="text">${data.reply}</div>
//             </div>`;
//         chatBox.scrollTop = chatBox.scrollHeight;
//     });

//     // Effacer l'entrée
//     document.getElementById("message").value = "";
// }


// function ajouterMessage(texte, type) {
//     const chat_box = document.getElementById("chat-box");
    
//     const div = document.createElement("div");
//     div.className = type === "user" ? "user-message" : "bot-message";
//     div.innerText = texte;
//     chat_box.appendChild(div);

//     chat_box.scrollTop = chat_box.scrollHeight;
// }



// async function chargerHistorique() {
//     const femme_id = localStorage.getItem("femme_id");

//     const response = await fetch(`/historique/${femme_id}`);
//     const data = await response.json();

//     if (data.status === "success") {
//         const messages = data.historique;

//         messages.forEach(msg => {
//             ajouterMessage(msg.question, "user");
//             ajouterMessage(msg.reponse, "bot");
//         });
//     }
// }

// window.onload = function() {
//     chargerHistorique();
// }
