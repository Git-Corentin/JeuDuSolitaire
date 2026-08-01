"""Modèle du solitaire (Klondike) : état de la partie et règles du jeu.

Ce module ne dépend **ni de tkinter ni d'aucune interface** : il peut être
utilisé, testé et exploré (par le solveur) sans écran.

Vocabulaire employé dans tout le projet :

* **colonne** : une des sept piles du tableau ;
* **pioche** : le talon de cartes non encore tirées ;
* **défausse** : les cartes tirées de la pioche (seule celle du dessus est jouable) ;
* **base** : une des quatre piles à construire de l'As au Roi.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from .cartes import SYMBOLES, Carte, couleurs_opposees, jeu_complet

# --------------------------------------------------------------------------
# Barème du score
# --------------------------------------------------------------------------

POINTS_DEFAUSSE_VERS_COLONNE = 5
POINTS_RETOURNEMENT = 5
POINTS_VERS_BASE = 10
POINTS_BASE_VERS_COLONNE = -15
PENALITE_RECYCLAGE = {1: -100, 3: -20}


# --------------------------------------------------------------------------
# Structures de base
# --------------------------------------------------------------------------


@dataclass
class Colonne:
    """Une pile du tableau : des cartes cachées surmontées de cartes visibles."""

    cachees: list[Carte] = field(default_factory=list)
    visibles: list[Carte] = field(default_factory=list)

    @property
    def est_vide(self) -> bool:
        return not self.cachees and not self.visibles

    @property
    def carte_libre(self) -> Carte | None:
        """Carte du bas de la colonne, la seule sur laquelle on peut poser."""
        return self.visibles[-1] if self.visibles else None

    @property
    def hauteur(self) -> int:
        return len(self.cachees) + len(self.visibles)

    def retourner_si_besoin(self) -> bool:
        """Retourne la carte cachée du dessous si la colonne n'a plus de carte
        visible. Renvoie ``True`` si un retournement a eu lieu."""
        if not self.visibles and self.cachees:
            self.visibles.append(self.cachees.pop())
            return True
        return False

    def copie(self) -> "Colonne":
        return Colonne(list(self.cachees), list(self.visibles))


@dataclass(frozen=True, slots=True)
class Coup:
    """Un déplacement élémentaire.

    ``origine`` et ``destination`` valent ``"colonne"``, ``"defausse"``,
    ``"base"`` ou ``"pioche"``. ``nb`` est le nombre de cartes déplacées
    (toujours 1 hors des déplacements colonne → colonne).
    """

    origine: str
    i_origine: int = -1
    destination: str = ""
    i_destination: int = -1
    nb: int = 1
    carte: Carte | None = None

    @property
    def est_pioche(self) -> bool:
        return self.origine == "pioche"

    def description(self) -> str:
        """Phrase lisible décrivant le coup (utilisée par l'aide)."""
        if self.est_pioche:
            return "Piocher une nouvelle carte."
        if self.origine == "colonne":
            source = f"la colonne {self.i_origine + 1}"
        elif self.origine == "defausse":
            source = "la défausse"
        else:
            source = f"la base de {SYMBOLES[self.i_origine]}"
        if self.destination == "colonne":
            dest = f"la colonne {self.i_destination + 1}"
        else:
            dest = f"la base de {SYMBOLES[self.i_destination]}"
        carte = f"{self.carte}" if self.carte else "la carte"
        pluriel = f" (et les {self.nb - 1} cartes suivantes)" if self.nb > 1 else ""
        return f"Déplacer {carte}{pluriel} de {source} vers {dest}."


# --------------------------------------------------------------------------
# Partie
# --------------------------------------------------------------------------


class Partie:
    """État complet d'une partie de solitaire et application des règles."""

    def __init__(self, cartes_par_tirage: int = 1, graine: int | None = None) -> None:
        if cartes_par_tirage not in (1, 3):
            raise ValueError("Le tirage doit valoir 1 ou 3 cartes.")
        self.cartes_par_tirage = cartes_par_tirage
        self.graine = graine
        self.colonnes: list[Colonne] = [Colonne() for _ in range(7)]
        self.pioche: list[Carte] = []
        self.defausse: list[Carte] = []
        self.bases: list[list[Carte]] = [[] for _ in range(4)]
        self.score = 0
        self.nb_coups = 0
        self.nb_recyclages = 0
        self._historique: list[tuple] = []
        self.etats_vus: set[int] = set()
        self.distribuer()

    # -- Mise en place ------------------------------------------------------

    def distribuer(self) -> None:
        """Mélange le paquet et effectue la donne initiale."""
        alea = random.Random(self.graine)
        paquet = jeu_complet()
        alea.shuffle(paquet)
        self.colonnes = [Colonne() for _ in range(7)]
        for i, colonne in enumerate(self.colonnes):
            for _ in range(i):
                colonne.cachees.append(paquet.pop())
            colonne.visibles.append(paquet.pop())
        self.pioche = paquet
        self.defausse = []
        self.bases = [[] for _ in range(4)]
        self.score = 0
        self.nb_coups = 0
        self.nb_recyclages = 0
        self._historique = []
        #: Empreintes des positions déjà traversées pendant la partie. Sert à
        #: l'indice pour ne jamais conseiller un coup qui ramène à une
        #: position déjà vue (les allers-retours sans fin).
        self.etats_vus = {hash(self.cle_etat())}

    # -- Accès pratiques ----------------------------------------------------

    @property
    def carte_defausse(self) -> Carte | None:
        return self.defausse[-1] if self.defausse else None

    def carte_base(self, rang: int) -> Carte | None:
        base = self.bases[rang]
        return base[-1] if base else None

    @property
    def est_gagnee(self) -> bool:
        return all(len(base) == 13 for base in self.bases)

    @property
    def nb_cartes_cachees(self) -> int:
        return sum(len(colonne.cachees) for colonne in self.colonnes)

    @property
    def est_ouverte(self) -> bool:
        """Vrai si plus aucune carte n'est cachée : la victoire est alors
        toujours atteignable."""
        return self.nb_cartes_cachees == 0

    def cartes_defausse_visibles(self) -> list[Carte]:
        """Les (au plus trois) cartes de la défausse effectivement dessinées."""
        nb = min(self.cartes_par_tirage, len(self.defausse), 3)
        return self.defausse[-nb:] if nb else []

    # -- Identité d'une position -------------------------------------------

    def cle_etat(self) -> tuple:
        """Clé canonique de la position courante.

        Deux positions de même clé sont *le même coup à jouer* : l'ordre des
        sept colonnes n'ayant aucune importance au jeu, elles sont triées.
        Sert à repérer qu'on tourne en rond (voir :attr:`etats_vus`).
        """
        colonnes = tuple(
            sorted(
                (tuple(c.cachees), tuple(c.visibles)) for c in self.colonnes
            )
        )
        return (
            colonnes,
            tuple(len(base) for base in self.bases),
            tuple(self.pioche),
            tuple(self.defausse),
        )

    # -- Tests de légalité --------------------------------------------------

    def peut_poser_sur_base(self, carte: Carte) -> bool:
        sommet = self.carte_base(carte.rang_symbole)
        if sommet is None:
            return carte.valeur == 1
        return carte.valeur == sommet.valeur + 1

    def peut_poser_sur_colonne(self, carte: Carte, i: int) -> bool:
        colonne = self.colonnes[i]
        if colonne.est_vide:
            return carte.valeur == 13
        libre = colonne.carte_libre
        if libre is None:  # colonne composée uniquement de cartes cachées
            return False
        return couleurs_opposees(carte, libre) and carte.valeur + 1 == libre.valeur

    def coup_valide(self, coup: Coup) -> bool:
        """Vérifie qu'un coup est jouable dans l'état courant."""
        if coup.est_pioche:
            return bool(self.pioche or self.defausse)
        carte = self._carte_source(coup)
        if carte is None:
            return False
        if coup.destination == "base":
            return coup.nb == 1 and self.peut_poser_sur_base(carte)
        if coup.destination == "colonne":
            if coup.origine == "colonne" and coup.i_origine == coup.i_destination:
                return False
            return self.peut_poser_sur_colonne(carte, coup.i_destination)
        return False

    def _carte_source(self, coup: Coup) -> Carte | None:
        """Première carte déplacée par le coup, ou ``None`` si le coup est
        impossible."""
        if coup.origine == "colonne":
            visibles = self.colonnes[coup.i_origine].visibles
            if len(visibles) < coup.nb or coup.nb < 1:
                return None
            return visibles[-coup.nb]
        if coup.origine == "defausse":
            return self.carte_defausse
        if coup.origine == "base":
            return self.carte_base(coup.i_origine)
        return None

    # -- Application des coups ---------------------------------------------

    def appliquer(self, coup: Coup) -> bool:
        """Joue un coup s'il est légal. Renvoie ``True`` en cas de succès."""
        if not self.coup_valide(coup):
            return False
        self._memoriser()
        if coup.est_pioche:
            self._piocher()
        else:
            cartes = self._prelever(coup)
            self._deposer(coup, cartes)
        self.nb_coups += 1
        self.etats_vus.add(hash(self.cle_etat()))
        return True

    def _piocher(self) -> None:
        if not self.pioche:
            # La défausse est retournée d'un bloc : la première carte tirée
            # se retrouve sur le dessus du talon, l'ordre est donc conservé.
            self.pioche = self.defausse
            self.defausse = []
            self.nb_recyclages += 1
            self._ajouter_score(PENALITE_RECYCLAGE[self.cartes_par_tirage])
            return
        for _ in range(self.cartes_par_tirage):
            if not self.pioche:
                break
            self.defausse.append(self.pioche.pop(0))

    def _prelever(self, coup: Coup) -> list[Carte]:
        if coup.origine == "colonne":
            colonne = self.colonnes[coup.i_origine]
            cartes = colonne.visibles[-coup.nb:]
            del colonne.visibles[-coup.nb:]
            if colonne.retourner_si_besoin():
                self._ajouter_score(POINTS_RETOURNEMENT)
            return cartes
        if coup.origine == "defausse":
            return [self.defausse.pop()]
        # origine == "base"
        return [self.bases[coup.i_origine].pop()]

    def _deposer(self, coup: Coup, cartes: list[Carte]) -> None:
        if coup.destination == "base":
            self.bases[cartes[0].rang_symbole].extend(cartes)
            self._ajouter_score(POINTS_VERS_BASE)
        else:
            self.colonnes[coup.i_destination].visibles.extend(cartes)
            if coup.origine == "defausse":
                self._ajouter_score(POINTS_DEFAUSSE_VERS_COLONNE)
            elif coup.origine == "base":
                self._ajouter_score(POINTS_BASE_VERS_COLONNE)

    def _ajouter_score(self, points: int) -> None:
        self.score = max(0, self.score + points)

    # -- Coups possibles ----------------------------------------------------

    def coups_legaux(self, inclure_pioche: bool = True) -> list[Coup]:
        """Tous les coups jouables dans l'état courant."""
        coups: list[Coup] = []

        # Colonnes -> bases et colonnes -> colonnes
        for i, colonne in enumerate(self.colonnes):
            if not colonne.visibles:
                continue
            libre = colonne.visibles[-1]
            if self.peut_poser_sur_base(libre):
                coups.append(
                    Coup("colonne", i, "base", libre.rang_symbole, 1, libre)
                )
            for nb in range(1, len(colonne.visibles) + 1):
                carte = colonne.visibles[-nb]
                for j in range(7):
                    if j != i and self.peut_poser_sur_colonne(carte, j):
                        coups.append(Coup("colonne", i, "colonne", j, nb, carte))

        # Défausse -> base / colonne
        carte = self.carte_defausse
        if carte is not None:
            if self.peut_poser_sur_base(carte):
                coups.append(
                    Coup("defausse", -1, "base", carte.rang_symbole, 1, carte)
                )
            for j in range(7):
                if self.peut_poser_sur_colonne(carte, j):
                    coups.append(Coup("defausse", -1, "colonne", j, 1, carte))

        # Bases -> colonnes
        for rang in range(4):
            carte = self.carte_base(rang)
            if carte is None:
                continue
            for j in range(7):
                if self.peut_poser_sur_colonne(carte, j):
                    coups.append(Coup("base", rang, "colonne", j, 1, carte))

        if inclure_pioche and (self.pioche or self.defausse):
            coups.append(Coup("pioche", -1, "defausse"))
        return coups

    # -- Historique ---------------------------------------------------------

    def _memoriser(self) -> None:
        self._historique.append(self.instantane())
        if len(self._historique) > 500:
            del self._historique[0]

    def instantane(self) -> tuple:
        """Copie profonde et légère de l'état, pour l'annulation."""
        return (
            tuple((tuple(c.cachees), tuple(c.visibles)) for c in self.colonnes),
            tuple(self.pioche),
            tuple(self.defausse),
            tuple(tuple(b) for b in self.bases),
            self.score,
            self.nb_coups,
            self.nb_recyclages,
        )

    def restaurer(self, instantane: tuple) -> None:
        colonnes, pioche, defausse, bases, score, nb_coups, nb_recyclages = instantane
        self.colonnes = [Colonne(list(c), list(v)) for c, v in colonnes]
        self.pioche = list(pioche)
        self.defausse = list(defausse)
        self.bases = [list(b) for b in bases]
        self.score = score
        self.nb_coups = nb_coups
        self.nb_recyclages = nb_recyclages

    @property
    def peut_annuler(self) -> bool:
        return bool(self._historique)

    def annuler(self) -> bool:
        """Revient à l'état précédant le dernier coup."""
        if not self._historique:
            return False
        # La position que l'on quitte n'a plus été « vue » : sans cela,
        # l'indice refuserait de reproposer le coup que l'on vient d'annuler.
        self.etats_vus.discard(hash(self.cle_etat()))
        self.restaurer(self._historique.pop())
        return True

    def copie(self) -> "Partie":
        """Copie indépendante de la partie (sans l'historique)."""
        autre = Partie.__new__(Partie)
        autre.cartes_par_tirage = self.cartes_par_tirage
        autre.graine = self.graine
        autre._historique = []
        autre.restaurer(self.instantane())
        autre.etats_vus = set(self.etats_vus)
        return autre

    # -- Divers -------------------------------------------------------------

    def __repr__(self) -> str:  # pragma: no cover - confort de débogage
        lignes = [f"<Partie score={self.score} coups={self.nb_coups}>"]
        for i, colonne in enumerate(self.colonnes):
            caches = "?" * len(colonne.cachees)
            visibles = " ".join(str(c) for c in colonne.visibles)
            lignes.append(f"  colonne {i + 1}: {caches} {visibles}")
        lignes.append(f"  pioche: {len(self.pioche)} / défausse: {len(self.defausse)}")
        lignes.append(
            "  bases: "
            + ", ".join(
                f"{SYMBOLES[r]}={len(self.bases[r])}" for r in range(4)
            )
        )
        return "\n".join(lignes)


__all__ = ["Colonne", "Coup", "Partie"]
