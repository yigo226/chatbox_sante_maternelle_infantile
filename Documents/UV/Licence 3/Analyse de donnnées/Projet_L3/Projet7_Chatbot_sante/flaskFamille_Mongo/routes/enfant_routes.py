from flask import Blueprint, render_template, request, redirect, session
from database import db
from models.enfant_model import age_en_mois, prochain_vaccin
from utils.vaccin_utils import creer_vaccin
from datetime import datetime
from utils.vaccin_utils import prochaine_vaccin_future
from dateutil.relativedelta import relativedelta
from bson import ObjectId

# Les Blueprint
femme_bp = Blueprint("femme_bp", __name__)
enfant_bp = Blueprint("enfant_bp", __name__)

@enfant_bp.route("/enfants/ajouter/<id>", methods=["GET", "POST"])
def ajouter_enfant(id):
    if request.method == "POST":
        naissance = request.form["naissance"]
        age = age_en_mois(naissance)

        vaccin, date_vaccin, rappels = prochain_vaccin(naissance, age)

        enfant = {
            "femme_id": id,
            "nom": request.form["nom"],
            "genre": request.form["genre"],
            "date_naissance": naissance,
            "age_mois": age,
        }

        db.db.enfants.insert_one(enfant)
        creer_vaccin(enfant)

        return redirect("/dashboard")

    return render_template("enfants/ajouter.html")




@enfant_bp.route("/dashboard/enfants")
def dashboard_enfants():
    if "femme" not in session:
        return redirect("/login")

    femme_id = session["femme"]["id"]

    # Tous les enfants liés à la femme
    enfants = list(db.db.enfants.find({"femme_id": femme_id}))

    # --- NOUVELLE VERSION -- fonctionne comme dashboard des femmes ---
    enfants_dashboard = []

    for enfant in enfants:

        # -------------------------
        # 1. Calcul de l'âge en mois
        # -------------------------
        try:
            date_naissance = datetime.strptime(enfant["date_naissance"], "%Y-%m-%d")
            delta = relativedelta(datetime.now(), date_naissance)
            age_mois = delta.years * 12 + delta.months
        except:
            age_mois = None

        # -------------------------
        # 2. Récupérer le document rappel_vaccins ENFANT
        # -------------------------
        vaccin_doc = db.db.rappels_vaccins.find_one({"enfant_id": str(enfant["_id"])})

        vaccins_liste = []
        # prochaine_desc = None
        # prochaine_date = None
        # rappels = []

        # -------------------------
        # 3. Charger toutes les dates stockées
        # -------------------------
        if vaccin_doc:
            index = 1
            while f"date_vaccin{index}" in vaccin_doc:
                
                vaccins_liste.append({
                    "description": vaccin_doc.get(f"desc_vaccin{index}"),
                    "date_vaccin": vaccin_doc.get(f"date_vaccin{index}"),
                    "rappel7": vaccin_doc.get(f"rappel7_vaccin{index}"),
                    "rappel2": vaccin_doc.get(f"rappel2_vaccin{index}")
                })
                index += 1

            # -------------------------
            # 4. Identifier le vaccin prochain
            # -------------------------
            prochaine_desc, prochaine_date, rappels = prochaine_vaccin_future(vaccin_doc)
        # -------------------------
        # 5. Construire un bloc enfant complet
        # -------------------------
        enfants_dashboard.append({
            "id": str(enfant["_id"]),
            "nom": enfant.get("nom"),
            "date_naissance": enfant.get("date_naissance"),
            "age_mois": age_mois,
            "vaccins": vaccins_liste,
            "prochain_desc": prochaine_desc,
            "prochain_date": prochaine_date,
            "rappels": rappels
        })

    # -------------------------
    # 6. Envoyer au template
    # -------------------------
    return render_template("enfants/dashboardenfant.html",
                           enfants=enfants_dashboard)



#
@enfant_bp.route("/details_enfant/<enfant_id>")
def details_enfant(enfant_id):
    # Vérifier si l'utilisateur est connecté
    if "femme" not in session:
        return redirect("/login")
    # Récupérer les données de l'enfant par son ID


    enfant = db.db.enfants.find_one({"_id": ObjectId(enfant_id)})

    #enfant = db.db.enfants.find_one({"_id":str(enfant_id) })
    # Hypothèse sur le modèle de données

    if not enfant:
        return render_template("404.html"), 404  # Ou une page d'erreur si l'enfant n'est pas trouvé

    # Récupérer les visites ou autres détails selon vos besoins
     # Remplir cette liste avec les visites de l'enfant, par exemple
    vaccins_doc = db.db.rappels_vaccins.find_one({"enfant_id": enfant_id})
    vaccins_liste = [] 
    #print("Doc des vaccins",vaccins_doc)
    if vaccins_doc:
        #print("Les vaccins",vaccins_doc)
        index=1
        while f"date_vaccin{index}" in vaccins_doc:
            vaccins_liste.append({
                "description": vaccins_doc.get(f"desc_vaccin{index}"),
                "date_vaccin": vaccins_doc.get(f"date_vaccin{index}"),
                "rappel7": vaccins_doc.get(f"rappel7_vaccin{index}"),
                "rappel2": vaccins_doc.get(f"rappel2_vaccin{index}")
                # Ajoutez d'autres champs nécessaires
            })
            index += 1
            #print(" Vaccins liste", vaccins_liste)
                 
    return render_template("enfants/details_vaccins_enfant.html", enfant=enfant, vaccins=vaccins_liste)
