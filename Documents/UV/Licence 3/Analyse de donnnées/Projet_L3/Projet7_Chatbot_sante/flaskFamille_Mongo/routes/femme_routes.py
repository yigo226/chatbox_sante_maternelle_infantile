from flask import Blueprint, render_template, request, redirect, session,jsonify
from database import db
from passlib.hash import pbkdf2_sha256
#from models.enfant_model import prochain_vaccin

from bson.objectid import ObjectId
from utils.grossesse_utils import prochaine_visite_future,creer_visites

femme_bp = Blueprint("femme_bp", __name__)

# ---------------------
# INSCRIPTION FEMME
# ---------------------
@femme_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        femme = {
            "nom": request.form["nom"],
            "prenom": request.form["prenom"],
            "email": request.form["email"],
            "telephone": request.form["telephone"],
            "password": pbkdf2_sha256.hash(request.form["password"]),
            "enceinte": request.form["enceinte"],
            "mois_grossesse": int(request.form["mois_grossesse"]) if request.form["enceinte"] == "oui" else None
        }

        db.db.femmes.insert_one(femme)

        if femme["enceinte"] == "oui":
            # création de la date de visite et des rappels de la femme enceinte
            creer_visites(femme)
        return redirect("/login")

    return render_template("signup.html")

# mise à jour 
@femme_bp.route("/update_enceinte", methods=["GET","POST"])
def update_enceinte():
    femme_id = session["femme"]["id"]  # récupérer l'utilisateur connecté

    femme = db.db.femmes.find_one({"_id": ObjectId(femme_id)})
    ancienne = femme.get("enceinte", "non")   # ancienne valeur

    nouvelle = request.form.get("enceinte")
    mois = request.form.get("mois_grossesse")

    update = {"enceinte": nouvelle}

    # Si elle dit OUI → on ajoute mois de grossesse
    if nouvelle == "oui":
        update["mois_grossesse"] = int(mois)

    # Mise à jour de la femme
    db.db.femmes.update_one(
        {"_id": ObjectId(femme_id)},
        {"$set": update}
    )

    # mettre à jour la variable femme pour être cohérent avec creer_visites()
    femme = db.db.femmes.find_one({"_id": ObjectId(femme_id)})

    # ⚠ Important : creer_visites reçoit l'objet femme complet
    # donc on lui envoie femme (et pas ID)
    if ancienne == "non" and nouvelle == "oui":
        creer_visites(femme)

    return render_template("mise_a_jour.html")


# ---------------------
# LOGIN
# ---------------------
@femme_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        femme = db.db.femmes.find_one({"email": request.form["email"]})
       
        if femme and pbkdf2_sha256.verify(request.form["password"], femme["password"]):
            session["femme"] = {
                "id": str(femme["_id"]),
                "nom": femme["nom"],
                "prenom":femme["prenom"],
                "email": femme["email"],
                }

            if femme.get("enceinte") == "oui":
                session["femme"].update({
                    "enceinte": True,
                })
            
            else:
                session["femme"]["enceinte"] = False
            
            return redirect("/index")
        return render_template("login.html", error="Email ou mot de passe incorrect.")
    return render_template("login.html")


# ---------------------
# LOGOUT
# ---------------------
@femme_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------------
# DASHBOARD
# ---------------------

# @femme_bp.route("/dashboard")
# def dashboard():
#     if "femme" not in session:
#         return redirect("/login")

#     femme_id = session["femme"]["id"]

#     # ---------------------
#     # Mise à jour de la date de rappel dans la base données
#     # ---------------------

#     femme = db.db.femmes.find_one({"email": session["femme"]["email"]})
#     # Mise à jour de la femme
    
#     if femme.get("enceinte") == "oui": 

#         mois_grossesse = femme.get("mois_grossesse", 0)

#     ##---- les visites  et rappels 

#         # Récupérer les rappels de visite et Date de vaccin
#         visites_doc = db.db.rappels_visites.find_one({"femme_id": femme_id})

#         visites_liste = []

#         if visites_doc:
#             index = 1
#             while f"date_visite{index}" in visites_doc:
#                 visites_liste.append({
#                     "mois_grossesse": visites_doc["mois_grossesse"],
#                     "description": visites_doc.get(f"desc_visite{index}"),
#                     "date_visite": visites_doc.get(f"date_visite{index}"),
#                     "rappel7": visites_doc.get(f"rappel7_visite{index}"),
#                     "rappel2": visites_doc.get(f"rappel2_visite{index}")
#                 })
#                 index += 1


#             # récupérer la prochaine visite
#             prochaine_desc, prochaine_date, rappels = prochaine_visite_future(visites_doc)
                    
#         return render_template("dashboard.html", 
#                                 visites=visites_liste,
#                                 visites_doc=visites_doc,
#                                         prochaine_desc=prochaine_desc,
#                                         prochaine_date=prochaine_date,
#                                         rappels=rappels,
#                                         )
#     # ---------------------
#     # Enfant Mise à jour de la date de rappel dans la BD
#     # ---------------------

#     enfants = list(db.db.enfants.find({"femme_id": femme_id}))
    
#     # Pour chaque enfant, 
#     for enfant in enfants:

#         # 1️⃣ Convertir l'âge
#         try:
#             date_naissance = datetime.strptime(enfant["date_naissance"], "%Y-%m-%d")
#         except:
#             continue  # si problème dans la date

#         age_mois = relativedelta(datetime.now(), date_naissance).years * 12 + \
#                    relativedelta(datetime.now(), date_naissance).months

#         # 2️⃣ Si aucun prochain vaccin → on passe à l'enfant suivant
#         if not enfant.get("date_vaccin"):  # None, "", ou absent
#             enfant["age_mois"] = age_mois
#             continue

#         # 3️⃣ Convertir la date de vaccin si elle existe
#         try:
#             date_vaccin = datetime.strptime(enfant["date_vaccin"], "%Y-%m-%d")
#         except:
#             continue  # erreur de format → on ignore

#         # 4️⃣ Vérifier si la date de vaccin est dépassée
#         if datetime.now().date() > date_vaccin.date():

#             # recalcul
#             vaccin, nouvelle_date, rappels = prochain_vaccin(
#                 enfant["date_naissance"],
#                 age_mois
#             )

#             # 5️⃣ Mise à jour BD
#             db.db.enfants.update_one(
#                 {"_id": enfant["_id"]},
#                 {
#                     "$set": {
#                         "age_mois": age_mois,
#                         "prochain_vaccin": vaccin,
#                         "date_vaccin": nouvelle_date,
#                         "rappels_vaccin": rappels
#                     }
#                 }
#             )

#             # 6️⃣ Mise à jour de l'objet enfant
#             enfant["age_mois"] = age_mois
#             enfant["prochain_vaccin"] = vaccin
#             enfant["date_vaccin"] = nouvelle_date
#             enfant["rappels_vaccin"] = rappels

#         else:
#             # On met juste l'âge à jour
#             enfant["age_mois"] = age_mois

#     return render_template("dashboardenfant.html", 
#                             enfants=enfants)

@femme_bp.route("/dashboard")
def dashboard():
    if "femme" not in session:
        return redirect("/login")

    femme_id = session["femme"]["id"]
    femme = db.db.femmes.find_one({"email": session["femme"]["email"]})
    
    if femme.get("enceinte") == "oui": 
        mois_grossesse = femme.get("mois_grossesse", 0)

        visites_doc = db.db.rappels_visites.find_one({"femme_id": femme_id})
        visites_liste = []

        if visites_doc:
            index = 1
            while f"date_visite{index}" in visites_doc:
                visites_liste.append({
                    "mois_grossesse": visites_doc["mois_grossesse"],
                    "description": visites_doc.get(f"desc_visite{index}"),
                    "date_visite": visites_doc.get(f"date_visite{index}"),
                    "rappel7": visites_doc.get(f"rappel7_visite{index}"),
                    "rappel2": visites_doc.get(f"rappel2_visite{index}")
                })
                index += 1

            prochaine_desc, prochaine_date, rappels = prochaine_visite_future(visites_doc)
                    
        return render_template("dashboard.html", 
                               visites=visites_liste,
                               visites_doc=visites_doc,
                               prochaine_desc=prochaine_desc,
                               prochaine_date=prochaine_date,
                               rappels=rappels)

    return redirect("/dashboard/enfants")  # Handle if not enceinte or other cases

@femme_bp.route("/historique/<femme_id>", methods=["GET"])
def historique(femme_id):
    messages = list(db.db.historique_chat.find(
        {"femme_id": femme_id}
    ).sort("date", 1))  # du plus ancien au plus récent
    
    # transformer l'_id en string
    for m in messages:
        #print("Question et réponse",m)
        m["_id"] = str(m["_id"])
    
    return  messages


@femme_bp.route("/historique/supprimer", methods=["POST"])
def supprimer_historique():
    # Vérifier que la femme est connectée
    if "femme" not in session:
        return jsonify({"status": "error", "message": "Non autorisé"}), 401

    femme_id = session["femme"]["id"]

    # Suppression de tout l'historique
    result = db.db.historique_chat.delete_many({"femme_id": femme_id})

    return jsonify({
        "status": "success",
        "message": f"{result.deleted_count} messages supprimés."
    })
