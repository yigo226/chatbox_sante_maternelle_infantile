from flask import Flask, request, jsonify, render_template,Blueprint,session
from database import db
from routes.femme_routes import historique
from datetime import datetime
import joblib
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
nlp = spacy.load("fr_core_news_sm")


chatbox_bp = Blueprint("chatbox_bp", __name__)

# --- Charger modèle et dataset ---
model_theme = joblib.load("chatbot/model_theme.pkl")
df = joblib.load("chatbot/intents_df.pkl")


# --- Fonction de prétraitement de la question---
def preprocess(text):
    doc = nlp(text.lower())
    tokens = [token.lemma_ for token in doc if not token.is_stop and not token.is_punct]
    return " ".join(tokens)

#Répondre
def get_response(user_question, threshold=0.3):
    user_question_clean = preprocess(user_question)
    
    # 1️⃣ Prédire le thème
    predicted_theme = model_theme.predict([user_question_clean])[0]
    
    # 2️⃣ Filtrer les questions du thème
    df_theme = df[df["Theme"] == predicted_theme].reset_index(drop=True)
    
    # 3️⃣ TF-IDF sur le thème
    vectorizer_theme = TfidfVectorizer()
    X_vect_theme = vectorizer_theme.fit_transform(df_theme["question_clean"])
    user_vect = vectorizer_theme.transform([user_question_clean])
    
    # 4️⃣ Similarité cosinus
    sim_scores = cosine_similarity(user_vect, X_vect_theme)
    best_idx = sim_scores.argmax()
    max_score = sim_scores[0][best_idx]
    
    # 5️⃣ Vérifier seuil
    if max_score < threshold:
        return "😔 Désolé, je ne suis pas sûr d’avoir bien compris votre question. Pouvez-vous reformuler s'il vous plaît ?"
    
    return df_theme.iloc[best_idx]["Reponse"]

# --- Route pour la page principale ---
@chatbox_bp.route("/index")
def index():
    if "femme" in session:
        femme_id = session["femme"]["id"]
        
        # Récupération de l'historique depuis MongoDB
        messages = historique(femme_id)
        return render_template("index_chatbox.html", messages=messages)
    else:
        return render_template("index_chatbox.html")
# ---------------------------------------
# 1) Chatbot 
# ---------------------------------------
# --- Route pour recevoir le message ---
# @chatbox_bp.route("/ask", methods=["POST"])
# def ask():
#     user_message = request.form.get("message")
#     if not user_message:
#         return jsonify({"reply": "Veuillez écrire une question."})
    
#     response = get_response(user_message)
#     return jsonify({"reply": response})



@chatbox_bp.route("/ask", methods=["POST"])
def ask():
    # La question de user
    user_message = request.form.get("message", "")
    if not user_message:
        return jsonify({"reply": "Veuillez écrire une question."})
    #Chercher la réponse
    response = get_response(user_message)
    #Hist
    if "femme" in session:
        femme_id = session["femme"]["id"]
        historique = {
            "femme_id": femme_id,
            "question": user_message,
            "reponse": response,
            "date": datetime.now()
        }

        db.db.historique_chat.insert_one(historique)

    return jsonify({"reply": response})
