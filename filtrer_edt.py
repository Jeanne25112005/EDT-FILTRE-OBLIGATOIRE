#!/usr/bin/env python3
"""
Filtre un flux iCal (ADE / Lyon 1) pour ne garder que les événements
dont le titre contient un mot-clé donné (par défaut : "OBLIGATOIRE").

Utilisation :
    python3 filtrer_edt.py

Il suffit de renseigner l'URL de ton flux ADE (celle que tu utilises
déjà pour t'abonner dans Apple Calendrier) dans la variable URL_SOURCE
ci-dessous, puis de lancer le script. Il produit un fichier
"edt_filtre.ics" contenant uniquement les événements obligatoires.
"""

import os
import sys
import urllib.request
from icalendar import Calendar

# -----------------------------------------------------------------
# CONFIGURATION - à adapter
# -----------------------------------------------------------------

# L'URL de ton flux ADE est lue depuis la variable d'environnement
# EDT_SOURCE_URL (stockée comme "secret" GitHub) plutôt qu'écrite ici
# en clair, pour éviter de l'exposer publiquement dans le code.
URL_SOURCE = os.environ.get("EDT_SOURCE_URL")

if not URL_SOURCE:
    sys.exit(
        "Erreur : la variable d'environnement EDT_SOURCE_URL n'est pas définie.\n"
        "En local : EDT_SOURCE_URL='https://...' python3 filtrer_edt.py\n"
        "Sur GitHub Actions : configure-la comme secret du repo."
    )

# Mot(s)-clé(s) qui identifient un événement obligatoire.
# Le test est insensible à la casse (majuscule/minuscule n'importe pas).
MOTS_CLES_OBLIGATOIRE = ["OBLIGATOIRE"]

# Nom du fichier de sortie généré
FICHIER_SORTIE = "edt_filtre.ics"

# -----------------------------------------------------------------
# SCRIPT
# -----------------------------------------------------------------

def telecharger_ics(url: str) -> bytes:
    """Télécharge le contenu brut du flux iCal source."""
    # webcal:// n'est pas un protocole HTTP standard pour urllib,
    # on le convertit donc en https:// pour le téléchargement.
    if url.startswith("webcal://"):
        url = "https://" + url[len("webcal://"):]
    with urllib.request.urlopen(url) as reponse:
        return reponse.read()


def est_obligatoire(titre: str) -> bool:
    """Vérifie si le titre de l'événement contient un des mots-clés."""
    titre_normalise = (titre or "").upper()
    return any(mot.upper() in titre_normalise for mot in MOTS_CLES_OBLIGATOIRE)


def filtrer_calendrier(contenu_ics: bytes) -> bytes:
    """Ne garde que les VEVENT dont le titre matche le(s) mot(s)-clé(s)."""
    cal_source = Calendar.from_ical(contenu_ics)

    cal_filtre = Calendar()
    # On recopie les métadonnées du calendrier d'origine (nom, fuseau horaire, etc.)
    for cle, valeur in cal_source.items():
        cal_filtre.add(cle, valeur)

    nb_total = 0
    nb_gardes = 0

    for composant in cal_source.walk():
        if composant.name == "VEVENT":
            nb_total += 1
            titre = str(composant.get("summary", ""))
            if est_obligatoire(titre):
                cal_filtre.add_component(composant)
                nb_gardes += 1
        elif composant.name != "VCALENDAR":
            # On garde les autres sous-composants éventuels (VTIMEZONE, etc.)
            cal_filtre.add_component(composant)

    print(f"{nb_gardes} événement(s) obligatoire(s) gardé(s) sur {nb_total} au total.")
    return cal_filtre.to_ical()


def main():
    print("Téléchargement du flux ADE...")
    contenu = telecharger_ics(URL_SOURCE)

    print("Filtrage des événements obligatoires...")
    contenu_filtre = filtrer_calendrier(contenu)

    with open(FICHIER_SORTIE, "wb") as f:
        f.write(contenu_filtre)

    print(f"Fichier généré : {FICHIER_SORTIE}")


if __name__ == "__main__":
    main()
