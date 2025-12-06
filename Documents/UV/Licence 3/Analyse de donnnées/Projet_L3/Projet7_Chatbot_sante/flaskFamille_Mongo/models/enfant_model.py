from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

CALENDRIER_VACCINS = {
    0: "BCG + VPO + Hépatite B",
    2: "Penta 1 + VPO 1 + PCV13 + Rota 1",
    3: "Penta 2 + VPO 2 + Rota 2",
    4: "Penta 3 + VPO 3 + PCV13 + Rota 3",
    9: "RR1 + VAA + PCV13 + VPI 2",
    15: "RR2 + MenA",
}

def age_en_mois(date_naissance):
    d = datetime.strptime(date_naissance, "%Y-%m-%d")
    today = datetime.now()
    return (today.year - d.year) * 12 + (today.month - d.month)


def prochain_vaccin(date_naissance, age_mois):
    date_naissance_dt = datetime.strptime(date_naissance, "%Y-%m-%d")

    for mois, vaccin in CALENDRIER_VACCINS.items():
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


def generer_vaccins_document(date_naissance):
    vaccins = {}
    naissance = datetime.strptime(date_naissance, "%Y-%m-%d")

    # Trie des vaccins dans l'ordre croissant
    calendrier_trie = sorted(CALENDRIER_VACCINS.items(), key=lambda x: x[0])

    for index, (mois, description) in enumerate(calendrier_trie, start=1):

        # Date du vaccin = date de naissance + mois correspondants
        date_vaccin = naissance + relativedelta(months=mois)

        # Stockage dans le dictionnaire final
        vaccins[f"date_vaccin{index}"] = date_vaccin.strftime("%Y-%m-%d")
        vaccins[f"desc_vaccin{index}"] = description

        # Rappels automatiques
        vaccins[f"rappel7_vaccin{index}"] = (date_vaccin - timedelta(days=7)).strftime("%Y-%m-%d")
        vaccins[f"rappel2_vaccin{index}"] = (date_vaccin - timedelta(days=2)).strftime("%Y-%m-%d")

    return vaccins

#test

#print(generer_vaccins_document("2025-09-10"))