from datetime import datetime, timedelta

CONSULT_CALENDAR = {
    1: "1ère visite : Avant 3 mois",
    4: "Échographie + contrôle croissance",
    5: "Analyse sang : anémie fer",
    6: "Dépistage antigène",
    7: "Échographie précision",
    8: "Consultation pré-anesthésique",
    9: "Dernière consultation"
}


def prochaine_visite(mois_grossesse):
    # Trouver le prochain mois du calendrier
    prochains_mois = sorted(month for month in CONSULT_CALENDAR.keys() if month > mois_grossesse)

    if not prochains_mois:  # Aucune visite prévue
        return None, None, None  

    mois_visite = prochains_mois[0]
    description = CONSULT_CALENDAR[mois_visite]

    # Date prévue pour la visite
    # Supposez qu'une visite a lieu 1 mois après le prochain mois de grossesse
    date_visite = datetime.now() + timedelta(days=(mois_visite - mois_grossesse) * 30)

    # Calcul des rappels
    rappel7 = date_visite - timedelta(days=7)
    rappel2 = date_visite - timedelta(days=2)

    return description, date_visite.strftime("%Y-%m-%d"), [
        rappel7.strftime("%Y-%m-%d"),
        rappel2.strftime("%Y-%m-%d")
    ]

# Générer  la date de visiste ( Tous les rappels)
def generer_visites_document(mois_grossesse):
    visites = {}
    maintenant = datetime.now()

    # mois de visite supérieurs au mois actuel
    prochains = sorted(m for m in CONSULT_CALENDAR if m > mois_grossesse)

    for index, mois_visite in enumerate(prochains, start=1):
        description = CONSULT_CALENDAR[mois_visite]

        # Calcul de la date de visite
        delta = (mois_visite - mois_grossesse) * 30
        date_visite = maintenant + timedelta(days=delta)

        # ajouter au dictionnaire
        visites[f"date_visite{index}"] = date_visite.strftime("%Y-%m-%d")
        visites[f"desc_visite{index}"] = description

        # rappels associés
        visites[f"rappel7_visite{index}"] = (date_visite - timedelta(days=7)).strftime("%Y-%m-%d")
        visites[f"rappel2_visite{index}"] = (date_visite - timedelta(days=2)).strftime("%Y-%m-%d")

    return visites
