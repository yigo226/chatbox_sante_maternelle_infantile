from datetime import datetime, timedelta
from flask import jsonify,request
from database import db
from models.enfant_model import generer_vaccins_document

VACCIN_CALENDAR = {
    0: "BCG + VPO + Hépatite B",
    2: "Penta 1 + VPO 1 + PCV13 + Rota 1",
    3: "Penta 2 + VPO 2 + Rota 2",
    4: "Penta 3 + VPO 3 + PCV13 + Rota 3",
    9: "RR1 + VAA + PCV13 + VPI 2",
    15: "RR2 + MenA",
}

def age_en_mois(date_naissance):
    return (datetime.now().date().year - date_naissance.year) * 12 + \
           (datetime.now().date().month - date_naissance.month)

from dateutil.relativedelta import relativedelta

def prochain_vaccin(date_naissance, age_mois):
    date_naissance_dt = datetime.strptime(date_naissance, "%Y-%m-%d")

    for mois, vaccin in VACCIN_CALENDAR.items():
        if age_mois < mois:
            date_vaccin = date_naissance_dt + relativedelta(months=+mois)

            rappel1 = date_vaccin - timedelta(days=7)
            rappel2 = date_vaccin - timedelta(days=2)

            return (
                vaccin,
                date_vaccin.strftime("%Y-%m-%d"),
                [
                    rappel1.strftime("%Y-%m-%d"),
                    rappel2.strftime("%Y-%m-%d")
                ]
            )

    return None, None, []


# 

#  : si tu récupères l'enfant via un formulaire POST
def creer_vaccin(enfant):
    #enfant = db.db.enfants.find_one({"id_mere": enfant["femme_id"]})

    if not enfant:
        return jsonify({"status": "error", "message": "Enfant introuvable"}), 404

    enfant_id = str(enfant["_id"])
    date_naissance = enfant["date_naissance"]

    vaccins = generer_vaccins_document(date_naissance)

    doc = {
        "enfant_id": enfant_id,
        "date_naissance": date_naissance,
        "date_creation": datetime.now().strftime("%Y-%m-%d"),
        **vaccins
    }

    db.db.rappels_vaccins.insert_one(doc)

    return jsonify({
        "status": "success",
        "message": "Tous les vaccins ont été enregistrés dans un seul document.",
        "total_vaccins": len([v for v in vaccins if v.startswith("date_vaccin")])
    })

# A 
def creer_rappel_vaccin(femme):
    femme = db.db.femmes.find_one({"email": request.form["email"]})
    femme_id = str(femme["_id"]),
    mois_grossesse = int(femme["mois_grossesse"])

    visites = generer_vaccins_document(mois_grossesse)

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

# def prochain_vaccin(age):
#     for mois, vaccin in VACCIN_CALENDAR.items():
#         if age < mois:
#             date = datetime.now() + timedelta(days=30)
#             rappel7 = date - timedelta(days=7)
#             rappel2 = date - timedelta(days=2)
#             return vaccin, date, [rappel7, rappel2]
#     return None, None, None
from datetime import datetime

def prochaine_vaccin_future(vaccins_doc):
    """
    Trouve le prochain vaccin non encore passé dans rappels_vaccins.
    Retourne: description, date_vaccin, [rappel7, rappel2]
    """

    if not vaccins_doc:
        return None, None, []

    vaccins = []
    index = 1

    # Lire tous les vaccins stockés
    while f"date_vaccin{index}" in vaccins_doc:
        date_str = vaccins_doc.get(f"date_vaccin{index}")
        desc = vaccins_doc.get(f"desc_vaccin{index}")
        rappel7 = vaccins_doc.get(f"rappel7_vaccin{index}")
        rappel2 = vaccins_doc.get(f"rappel2_vaccin{index}")

        if date_str:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            vaccins.append((date_obj, desc, rappel7, rappel2))

        index += 1

    if not vaccins:
        return None, None, []

    # Filtrer les dates futures
    now = datetime.now()
    vaccins_futurs = [v for v in vaccins if v[0] >= now]

    if not vaccins_futurs:
        return None, None, []

    # Prendre le vaccin le plus proche dans le futur
    prochain = sorted(vaccins_futurs, key=lambda v: v[0])[0]

    return (
        prochain[1],                        # description
        prochain[0].strftime("%Y-%m-%d"),   # date_vaccin
        [prochain[2], prochain[3]]          # rappels
    )
