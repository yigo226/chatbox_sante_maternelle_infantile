from flask import Blueprint, render_template, request, redirect, session,jsonify
from database import db
from passlib.hash import pbkdf2_sha256
from models.femme_model import prochaine_visite,generer_visites_document
from datetime import datetime
from dateutil.relativedelta import relativedelta
from bson.objectid import ObjectId


femme_bp = Blueprint("femme_bp", __name__)

def creer_visites(femme):
    femme = db.db.femmes.find_one({"email": request.form["email"]})
    femme_id = str(femme["_id"]),
    mois_grossesse = int(femme["mois_grossesse"])

    visites = generer_visites_document(mois_grossesse)

    # structure du document final
    doc = {
        "femme_id": femme_id,
        "mois_grossesse": mois_grossesse,
        "date_creation": datetime.now().strftime("%Y-%m-%d"),
        **visites
    }

    db.db.rappels_visites.insert_one(doc)

    return jsonify({
        "status": "success",
        "message": "Toutes les visites ont été enregistrées dans un seul document.",
        "total_visites": len([v for v in visites if v.startswith("date_visite")])
    })


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

        # Grossesse
        if femme["enceinte"] == "oui":
            visite, date_visite, rappels = prochaine_visite(femme["mois_grossesse"])
            femme["prochaine_visite"] = visite
            femme["date_visite"] = date_visite
            femme["rappels_visite"] = rappels

        db.db.femmes.insert_one(femme)

        creer_visites(femme)

        session["femme"] = {
                "id": str(femme["_id"]),  # ❤️ la correction essentielle
                "nom": femme["nom"],
                "prenom": femme["prenom"],
                "email": femme["email"],
            }
        return redirect("/login")

    return render_template("signup.html")


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
            #if session[femme.enceinte]==True:

            # if femme.get("enceinte") == "oui":
                
            #     # Si aucune visite n’est encore calculée
            #     if not femme.get("date_visite"):

            #         visite, date_visite, rappels = prochaine_visite(femme["mois_grossesse"])

            #         db.db.femmes.update_one(
            #             {"_id": femme["_id"]},
            #             {"$set": {
            #                 "prochaine_visite": visite,
            #                 "date_visite": date_visite,
            #                 "rappels_visite": rappels
            #             }}
            #         )

            #         session["femme"].update({
            #             "enceinte": True,
            #             "mois_grossesse": femme["mois_grossesse"],
            #             "prochaine_visite": visite,
            #             "date_visite": date_visite,
            #             "rappels_visite": rappels
            #         })


            if femme.get("enceinte") == "oui":
                session["femme"].update({
                    "enceinte": True,
                    "mois_grossesse": femme.get("mois_grossesse"),
                    "prochaine_visite": femme.get("prochaine_visite"),
                    "date_visite": femme.get("date_visite"),
                    "rappels_visite": femme.get("rappels_visite"),
                })
            
            else:
                session["femme"]["enceinte"] = False
          
            return redirect("/dashboard")
        
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

@femme_bp.route("/dashboard")
def dashboard():
    if "femme" not in session:
        return redirect("/login")

    femme_id = session["femme"]["id"]

    # ---------------------
    # Mise à jour de la date de rappel dans la base données
    # ---------------------

    femme = db.db.femmes.find_one({"email": session["femme"]["email"]})
    # Mise à jour de la femme
    
    if femme.get("enceinte") == "oui": 

        mois_grossesse = femme.get("mois_grossesse", 0)

        # Calculer la date de visite et les rappels
        #description, date_visite, rappels = prochaine_visite(mois_grossesse)
        date_visite = femme.get("date_visite") if femme else None
        rappels = femme.get("rappels_visite") if femme else []
        # Vérifier si la date de visite est dépassée
        if date_visite:
            date_visite_dt = datetime.strptime(date_visite, "%Y-%m-%d")

            if datetime.now().date() >= date_visite_dt.date():  # Si la date n'est pas passée
                description,date_visite, rappels = prochaine_visite(mois_grossesse)
                # Mettre à jour la base de données
                db.db.femmes.update_one(
                    {"_id": femme["_id"]},
                    {
                        "$set": {
                            "date_visite": date_visite,
                            
                            "rappels_visite": rappels,
                        }
                    }
                )
                # Mise à jour de l'objet femme dans la session
                session["femme"].update({
                    "date_visite": date_visite,
                    "rappels_visite": rappels,
                })

## 

# Récupérer le document des visites
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
    # ---------------------
    # Enfant Mise à jour de la date de rappel dans la BD
    # ---------------------

    enfants = list(db.db.enfants.find({"femme_id": femme_id}))
    
    # Pour chaque enfant, 
    for enfant in enfants:

        # 1️⃣ Convertir l'âge
        try:
            date_naissance = datetime.strptime(enfant["date_naissance"], "%Y-%m-%d")
        except:
            continue  # si problème dans la date

        age_mois = relativedelta(datetime.now(), date_naissance).years * 12 + \
                   relativedelta(datetime.now(), date_naissance).months

        # 2️⃣ Si aucun prochain vaccin → on passe à l'enfant suivant
        if not enfant.get("date_vaccin"):  # None, "", ou absent
            enfant["age_mois"] = age_mois
            continue

        # 3️⃣ Convertir la date de vaccin si elle existe
        try:
            date_vaccin = datetime.strptime(enfant["date_vaccin"], "%Y-%m-%d")
        except:
            continue  # erreur de format → on ignore

        # 4️⃣ Vérifier si la date de vaccin est dépassée
        if datetime.now().date() > date_vaccin.date():

            # recalcul
            vaccin, nouvelle_date, rappels = prochaine_visite(
                enfant["date_naissance"],
                age_mois
            )

            # 5️⃣ Mise à jour BD
            db.db.enfants.update_one(
                {"_id": enfant["_id"]},
                {
                    "$set": {
                        "age_mois": age_mois,
                        "prochain_vaccin": vaccin,
                        "date_vaccin": nouvelle_date,
                        "rappels_vaccin": rappels
                    }
                }
            )

            # 6️⃣ Mise à jour de l'objet enfant
            enfant["age_mois"] = age_mois
            enfant["prochain_vaccin"] = vaccin
            enfant["date_vaccin"] = nouvelle_date
            enfant["rappels_vaccin"] = rappels

        else:
            # On met juste l'âge à jour
            enfant["age_mois"] = age_mois

    return render_template("dashboard.html", visites=visites_liste, enfants=enfants)

