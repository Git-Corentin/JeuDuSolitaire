"""Représentation d'une carte à jouer.

Une :class:`Carte` est un objet immuable (donc hachable), ce qui permet de
l'utiliser comme clé de dictionnaire et dans les états explorés par le solveur.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Ordre de référence des symboles (celui des bases, de gauche à droite).
SYMBOLES = ("coeur", "carreau", "trefle", "pique")

#: Symboles rouges.
SYMBOLES_ROUGES = frozenset({"coeur", "carreau"})

#: Rang de chaque symbole, utilisé pour indexer les bases.
RANG_SYMBOLE = {symbole: rang for rang, symbole in enumerate(SYMBOLES)}

#: Nom des figures utilisé dans le nom des fichiers image.
NOMS_VALEURS = {1: "A", 11: "J", 12: "Q", 13: "K"}
VALEURS_DEPUIS_NOM = {nom: valeur for valeur, nom in NOMS_VALEURS.items()}

ROUGE = "rouge"
NOIR = "noir"


@dataclass(frozen=True, slots=True)
class Carte:
    """Une carte, caractérisée par sa valeur (1 = As, 13 = Roi) et son symbole."""

    valeur: int
    symbole: str

    def __post_init__(self) -> None:
        if not 1 <= self.valeur <= 13:
            raise ValueError(f"Valeur de carte invalide : {self.valeur}")
        if self.symbole not in RANG_SYMBOLE:
            raise ValueError(f"Symbole de carte invalide : {self.symbole}")

    # -- Propriétés ---------------------------------------------------------

    @property
    def est_rouge(self) -> bool:
        return self.symbole in SYMBOLES_ROUGES

    @property
    def couleur(self) -> str:
        """``"rouge"`` ou ``"noir"``."""
        return ROUGE if self.est_rouge else NOIR

    @property
    def rang_symbole(self) -> int:
        """Indice du symbole, c'est-à-dire de la base correspondante."""
        return RANG_SYMBOLE[self.symbole]

    @property
    def nom(self) -> str:
        """Nom du fichier image associé, par exemple ``"10_coeur"``."""
        return f"{NOMS_VALEURS.get(self.valeur, str(self.valeur))}_{self.symbole}"

    # -- Construction / affichage ------------------------------------------

    @classmethod
    def depuis_nom(cls, nom: str) -> "Carte":
        """Construit une carte à partir d'un nom du type ``"Q_pique"``."""
        valeur_texte, symbole = nom.split("_")
        valeur = VALEURS_DEPUIS_NOM.get(valeur_texte)
        if valeur is None:
            valeur = int(valeur_texte)
        return cls(valeur, symbole)

    def __str__(self) -> str:
        return self.nom


def jeu_complet() -> list[Carte]:
    """Renvoie les 52 cartes du jeu, dans l'ordre canonique."""
    return [Carte(valeur, symbole) for symbole in SYMBOLES for valeur in range(1, 14)]


def couleurs_opposees(a: Carte, b: Carte) -> bool:
    """Indique si les deux cartes sont de couleurs opposées."""
    return a.est_rouge != b.est_rouge
