
from datetime import datetime, timedelta
from flask import jsonify,request
from database import db
from models.femme_model import generer_visites_document
from datetime import datetime

# Le calendrier
CALENDRIER_PRENATAL = {
    1: "Avant le 3e mois : Évaluation des besoins.",
    4: "Échographie : taille du bébé.",
    5: "Prise de sang : recherche d’anémie.",
    6: "Prise de sang + dépistage antigène.",
    7: "Échographie précision : placenta + position bébé.",
    8: "Consultation pré-anesthésique.",
    9: "Dernière consultation de suivi."
}

## Prochaine visite la plus proche
def prochaine_visite_future(visites_doc):
    """
    Trouve la prochaine visite non encore passée dans rappels_visites.
    Retourne: description, date_visite, [rappel7, rappel2]
    """
    if not visites_doc:
        return None, None, []

    visites = []
    index = 1

    # Lire toutes les visites stockées
    while f"date_visite{index}" in visites_doc:
        date_str = visites_doc.get(f"date_visite{index}")
        desc = visites_doc.get(f"desc_visite{index}")
        rappel7 = visites_doc.get(f"rappel7_visite{index}")
        rappel2 = visites_doc.get(f"rappel2_visite{index}")

        if date_str:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            visites.append((date_obj, desc, rappel7, rappel2))
        
        index += 1

    if not visites:
        return None, None, []

    # Trier par date future
    now = datetime.now()
    visites_futures = [v for v in visites if v[0] >= now]

    if not visites_futures:
        return None, None, []

    # Prendre la plus proche
    prochaines = sorted(visites_futures, key=lambda v: v[0])[0]

    return (
        prochaines[1],                    # description
        prochaines[0].strftime("%Y-%m-%d"),  # date_visite
        [prochaines[2], prochaines[3]]    # rappels
    )


# Pour les rappels
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
