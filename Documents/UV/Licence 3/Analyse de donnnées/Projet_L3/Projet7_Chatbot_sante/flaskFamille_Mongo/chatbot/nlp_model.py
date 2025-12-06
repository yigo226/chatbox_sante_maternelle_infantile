import joblib
import spacy
import difflib

# Charger SpaCy (français)
try:
    nlp = spacy.load("fr_core_news_sm")
except:
    nlp = None  # Si SpaCy n'est pas installé, fallback simple


# -------------------------------------------------------------------
# Charger les modèles entraînés (TF-IDF + SVM + dataframe)
# -------------------------------------------------------------------
model_theme = joblib.load("chatbot/model_theme.pkl")
vectorizer_all = joblib.load("chatbot/vectorizer_all.pkl")
df = joblib.load("chatbot/intents_df.pkl")


# -------------------------------------------------------------------
# 1. Mapping question → réponse EXACT
# -------------------------------------------------------------------
mapping_questions = {
    q.lower(): row["reponse"]
    for _, row in df.iterrows()
    for q in [row["Question"]]
}


# -------------------------------------------------------------------
# 2. Mécanisme fuzzy (similarité)
# -------------------------------------------------------------------
def fuzzy_match(question):
    questions_list = list(mapping_questions.keys())
    match = difflib.get_close_matches(question.lower(), questions_list, n=1, cutoff=0.75)
    if match:
        return mapping_questions[match[0]]
    return None


# -------------------------------------------------------------------
# 3. Détection du thème (SVM + TF-IDF)
# -------------------------------------------------------------------
def predire_theme(question):
    vect = vectorizer_all.transform([question])
    theme = model_theme.predict(vect)[0]
    return theme


# -------------------------------------------------------------------
# 4. Obtenir une réponse basée sur le thème
# -------------------------------------------------------------------
def reponse_par_theme(theme):
    # prendre une ligne du dataframe
    ligne = df[df["Theme"] == theme].sample(1).iloc[0]
    return ligne["Reponse"]


# -------------------------------------------------------------------
# 5. Fonction principale utilisée par Flask
# -------------------------------------------------------------------
def get_chatbot_response(message):

    message_clean = message.lower().strip()

    # 1️⃣ Matching exact
    if message_clean in mapping_questions:
        return mapping_questions[message_clean]

    # 2️⃣ Matching fuzzy (similarité)
    fuzzy = fuzzy_match(message_clean)
    if fuzzy:
        return fuzzy

    # 3️⃣ Prédiction du thème avec TF-IDF + SVM
    theme = predire_theme(message_clean)
    reply = reponse_par_theme(theme)

    if reply:
        return reply

    # 4️⃣ Fallback final
    return ("Je ne suis pas sûr d’avoir bien compris votre question. "
            "Pouvez-vous reformuler s'il vous plaît ?")
