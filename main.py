#!/usr/bin/env python3
"""Point d'entrée du jeu du solitaire.

Exemples :

    python main.py                 # partie classique, tirage par 1
    python main.py --tirage 3      # tirage par 3 cartes
    python main.py --graine 42     # rejouer exactement la même donne
    python main.py --echelle 1/2   # forcer la taille d'affichage
"""

from __future__ import annotations

import argparse
import sys


def analyser_arguments(argv=None) -> argparse.Namespace:
    analyseur = argparse.ArgumentParser(description="Jeu du solitaire (Klondike).")
    analyseur.add_argument(
        "--tirage",
        type=int,
        choices=(1, 3),
        default=1,
        help="nombre de cartes retournées à chaque pioche (défaut : 1)",
    )
    analyseur.add_argument(
        "--graine",
        type=int,
        default=None,
        help="graine du mélange, pour rejouer une donne identique",
    )
    analyseur.add_argument(
        "--echelle",
        default=None,
        help="échelle d'affichage sous la forme num/den, par exemple 3/4 "
        "(par défaut, elle est déduite de la taille de l'écran)",
    )
    analyseur.add_argument(
        "--images",
        default=None,
        help="chemin du dossier contenant les images",
    )
    return analyseur.parse_args(argv)


def lire_echelle(texte: str | None):
    if texte is None:
        return None
    try:
        if "/" in texte:
            num, den = texte.split("/")
            return int(num), int(den)
        return int(texte), 1
    except ValueError:
        raise SystemExit(f"Échelle invalide : {texte!r} (attendu : 3/4, 1/2, 1…)")


def main(argv=None) -> int:
    arguments = analyser_arguments(argv)
    from solitaire.assets import ImagesIntrouvables
    from solitaire.ui import Application

    try:
        application = Application(
            tirage=arguments.tirage,
            graine=arguments.graine,
            echelle=lire_echelle(arguments.echelle),
            dossier_images=arguments.images,
        )
    except ImagesIntrouvables as erreur:
        print(f"Erreur : {erreur}", file=sys.stderr)
        return 1
    application.lancer()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
