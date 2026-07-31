"""Chargement des images du jeu et gestion du facteur d'échelle.

tkinter ne sait redimensionner une ``PhotoImage`` que par des rapports entiers
(``zoom`` agrandit, ``subsample`` réduit). On combine les deux pour obtenir une
échelle fractionnaire — par exemple 3/4 — choisie en fonction de la taille de
l'écran, de façon que le jeu tienne aussi bien sur un 1920x1080 que sur un
écran de portable plus modeste.
"""

from __future__ import annotations

from pathlib import Path
from tkinter import PhotoImage, TclError

from . import config
from .cartes import SYMBOLES, jeu_complet


class ImagesIntrouvables(RuntimeError):
    """Levée lorsque le dossier d'images est absent ou incomplet."""


def trouver_dossier_images(dossier: str | Path | None = None) -> Path:
    """Renvoie le premier dossier d'images existant."""
    candidats = [Path(dossier)] if dossier else list(config.DOSSIERS_IMAGES)
    for chemin in candidats:
        if chemin.is_dir():
            return chemin
    liste = "\n  - ".join(str(c) for c in candidats)
    raise ImagesIntrouvables(
        "Impossible de trouver le dossier des images. Emplacements testés :\n  - "
        + liste
    )


def choisir_echelle(largeur: int, hauteur: int) -> tuple[int, int]:
    """Plus grande échelle autorisée tenant dans ``largeur`` x ``hauteur``."""
    for num, den in config.ECHELLES:
        if (
            config.LARGEUR_REFERENCE * num / den <= largeur
            and config.HAUTEUR_REFERENCE * num / den <= hauteur
        ):
            return num, den
    return config.ECHELLES[-1]


class Ressources:
    """Toutes les images du jeu, déjà mises à l'échelle.

    Les ``PhotoImage`` doivent rester référencées tant qu'elles sont affichées :
    c'est le rôle de cet objet, conservé par la fenêtre principale.
    """

    def __init__(self, dossier: str | Path | None = None, echelle: tuple[int, int] = (1, 1)):
        self.dossier = trouver_dossier_images(dossier)
        self.num, self.den = echelle
        #: Décalage global (en pixels écran) appliqué à toutes les positions,
        #: pour centrer le jeu dans la fenêtre.
        self.decalage_x = 0
        self.decalage_y = 0

        self.cartes = {
            carte.nom: self._charger(f"{carte.nom}.png") for carte in jeu_complet()
        }
        self.dos = self._charger("dos2.png")
        self.dos_alternatif = self._charger("dos.png")
        self.retourne = self._charger("retourne.png")
        self.vide = self._charger("vide.png")
        self.bases = [self._charger(f"base_{symbole}.png") for symbole in SYMBOLES]
        self.reperes = [self._charger(f"repere{n}.png") for n in range(1, 14)]
        self.logo = self._charger("solitaire.png")
        self.jouer = self._charger("jouer.png")
        self.parametre = self._charger("parametre.png")
        self.indice_actif = self._charger("indice_select.png")
        self.indice_inactif = self._charger("indice_deselect.png")
        self.une_carte = self._charger("une_carte.png")
        self.une_carte_off = self._charger("une_carte_deselect.png")
        self.trois_cartes = self._charger("trois_cartes.png")
        self.trois_cartes_off = self._charger("trois_cartes_deselect.png")

    # -- Chargement ---------------------------------------------------------

    def _charger(self, nom_fichier: str) -> PhotoImage:
        chemin = self.dossier / nom_fichier
        if not chemin.is_file():
            raise ImagesIntrouvables(f"Image manquante : {chemin}")
        try:
            image = PhotoImage(file=str(chemin))
        except TclError as erreur:  # format illisible par Tk
            raise ImagesIntrouvables(
                f"Tk n'arrive pas à lire {chemin} ({erreur}). Les images doivent "
                "être au format PNG ou GIF (Tk 8.6) : vérifiez que le fichier "
                "n'est pas un JPEG renommé."
            ) from erreur
        if (self.num, self.den) == (1, 1):
            return image
        if self.num != 1:
            image = image.zoom(self.num)
        if self.den != 1:
            image = image.subsample(self.den)
        return image

    # -- Conversion des coordonnées ----------------------------------------

    def px(self, valeur: float) -> int:
        """Convertit une longueur de référence en pixels écran."""
        return round(valeur * self.num / self.den)

    def point(self, coord: tuple[float, float]) -> tuple[int, int]:
        """Convertit une position de référence en position écran."""
        return (
            self.px(coord[0]) + self.decalage_x,
            self.px(coord[1]) + self.decalage_y,
        )

    def centrer(self, largeur: int, hauteur: int) -> None:
        """Centre la zone de jeu dans une fenêtre de taille donnée."""
        self.decalage_x = max(0, (largeur - self.px(config.LARGEUR_REFERENCE)) // 2)
        self.decalage_y = max(0, (hauteur - self.px(config.HAUTEUR_REFERENCE)) // 2)

    @property
    def largeur_carte(self) -> int:
        return self.px(config.LARGEUR_CARTE)

    @property
    def hauteur_carte(self) -> int:
        return self.px(config.HAUTEUR_CARTE)

    def repere(self, nb_cartes: int) -> PhotoImage:
        """Image de repère couvrant ``nb_cartes`` cartes empilées."""
        return self.reperes[max(0, min(12, nb_cartes - 1))]
