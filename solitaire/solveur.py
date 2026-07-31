"""Aide au joueur : indice « meilleur coup » et analyse de solvabilité.

Deux services sont rendus :

* :func:`meilleur_coup` : choix instantané, purement heuristique, du coup le
  plus utile dans la position courante (bouton « Indice ») ;
* :func:`analyser` : exploration exhaustive (avec budget de temps et de nœuds)
  de l'arbre de jeu pour savoir si la partie est **encore gagnable**, et si oui
  renvoyer la suite de coups qui mène à la victoire (bouton « Analyse »).

La recherche travaille sur une représentation compacte de l'état (des tuples
d'entiers) : c'est indispensable pour pouvoir en explorer des centaines de
milliers. Les coups trouvés sont ensuite reconvertis en objets
:class:`~solitaire.partie.Coup` en les rejouant sur une copie de la partie.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from .cartes import Carte
from .config import MAX_NOEUDS_SOLVEUR, MAX_SECONDES_SOLVEUR
from .partie import Coup, Partie

# --------------------------------------------------------------------------
# Représentation compacte
# --------------------------------------------------------------------------
# Une carte est codée par un entier : rang_symbole * 13 + (valeur - 1).
# valeur(c) = c % 13 + 1 ; symbole(c) = c // 13 ; rouge(c) = c < 26.


def _code(carte: Carte) -> int:
    return carte.rang_symbole * 13 + carte.valeur - 1


def _valeur(c: int) -> int:
    return c % 13 + 1


def _rouge(c: int) -> bool:
    return c < 26


def etat_compact(partie: Partie) -> tuple:
    """Convertit une partie en état exploitable par la recherche."""
    colonnes = tuple(
        (
            tuple(_code(x) for x in col.cachees),
            tuple(_code(x) for x in col.visibles),
        )
        for col in partie.colonnes
    )
    bases = tuple(len(base) for base in partie.bases)
    pioche = tuple(_code(x) for x in partie.pioche)
    defausse = tuple(_code(x) for x in partie.defausse)
    return colonnes, bases, pioche, defausse


def _cle(etat: tuple) -> tuple:
    """Clé canonique : l'ordre des colonnes n'a aucune importance au jeu."""
    colonnes, bases, pioche, defausse = etat
    return tuple(sorted(colonnes)), bases, pioche, defausse


def _gagne(etat: tuple) -> bool:
    return etat[1] == (13, 13, 13, 13)


def _ouvert(etat: tuple) -> bool:
    """Aucune carte face cachée ne subsiste."""
    return all(not cachees for cachees, _ in etat[0])


# -- Codes de coups compacts ------------------------------------------------
# ("cb", i)          colonne i -> base
# ("cc", i, j, nb)   nb cartes de la colonne i -> colonne j
# ("db",)            défausse -> base
# ("dc", j)          défausse -> colonne j
# ("bc", r, j)       base r -> colonne j
# ("p",)             piocher


def _appliquer_compact(etat: tuple, coup: tuple, tirage: int) -> tuple:
    colonnes, bases, pioche, defausse = etat
    type_coup = coup[0]

    if type_coup == "p":
        if not pioche:
            return colonnes, bases, defausse, ()
        n = min(tirage, len(pioche))
        return colonnes, bases, pioche[n:], defausse + pioche[:n]

    cols = list(colonnes)

    def retirer(i: int, nb: int) -> tuple[int, ...]:
        cachees, visibles = cols[i]
        groupe = visibles[len(visibles) - nb:]
        restant = visibles[: len(visibles) - nb]
        if not restant and cachees:  # retournement automatique
            cols[i] = (cachees[:-1], (cachees[-1],))
        else:
            cols[i] = (cachees, restant)
        return groupe

    if type_coup == "cb":
        i = coup[1]
        (carte,) = retirer(i, 1)
        rang = carte // 13
        bases = bases[:rang] + (bases[rang] + 1,) + bases[rang + 1:]
        return tuple(cols), bases, pioche, defausse

    if type_coup == "cc":
        _, i, j, nb = coup
        groupe = retirer(i, nb)
        cachees, visibles = cols[j]
        cols[j] = (cachees, visibles + groupe)
        return tuple(cols), bases, pioche, defausse

    if type_coup == "db":
        carte = defausse[-1]
        rang = carte // 13
        bases = bases[:rang] + (bases[rang] + 1,) + bases[rang + 1:]
        return colonnes, bases, pioche, defausse[:-1]

    if type_coup == "dc":
        j = coup[1]
        carte = defausse[-1]
        cachees, visibles = cols[j]
        cols[j] = (cachees, visibles + (carte,))
        return tuple(cols), bases, pioche, defausse[:-1]

    if type_coup == "bc":
        _, r, j = coup
        carte = r * 13 + bases[r] - 1
        bases = bases[:r] + (bases[r] - 1,) + bases[r + 1:]
        cachees, visibles = cols[j]
        cols[j] = (cachees, visibles + (carte,))
        return tuple(cols), bases, pioche, defausse

    raise ValueError(f"Coup inconnu : {coup}")


def _est_sur(carte: int, bases: tuple) -> bool:
    """Règle classique de « montée sûre » : monter cette carte sur sa base ne
    peut jamais priver le tableau d'une carte utile."""
    v = _valeur(carte)
    if v <= 2:
        return True
    if _rouge(carte):
        opposees = (bases[2], bases[3])
        meme = bases[1] if carte < 13 else bases[0]
    else:
        opposees = (bases[0], bases[1])
        meme = bases[3] if carte < 39 else bases[2]
    return min(opposees) >= v - 1 and meme >= v - 2


def _coups_compacts(etat: tuple, tirage: int) -> list[tuple]:
    """Coups légaux, déjà triés du plus prometteur au moins prometteur."""
    colonnes, bases, pioche, defausse = etat

    # 1. Montées « sûres » : elles sont forcées, inutile de brancher.
    for i, (_, visibles) in enumerate(colonnes):
        if visibles:
            c = visibles[-1]
            if bases[c // 13] == _valeur(c) - 1 and _est_sur(c, bases):
                return [("cb", i)]
    if defausse:
        c = defausse[-1]
        if bases[c // 13] == _valeur(c) - 1 and _est_sur(c, bases):
            return [("db",)]

    montees, decouvertes, autres, vides, retours = [], [], [], [], []

    # 2. Montées sur les bases depuis le tableau et la défausse.
    for i, (_, visibles) in enumerate(colonnes):
        if visibles:
            c = visibles[-1]
            if bases[c // 13] == _valeur(c) - 1:
                montees.append(("cb", i))
    if defausse:
        c = defausse[-1]
        if bases[c // 13] == _valeur(c) - 1:
            montees.append(("db",))

    # 3. Déplacements entre colonnes.
    for i, (cachees, visibles) in enumerate(colonnes):
        for k in range(len(visibles)):
            tete = visibles[k]
            nb = len(visibles) - k
            deplace_tout = k == 0 and not cachees
            for j, (cachees_j, visibles_j) in enumerate(colonnes):
                if j == i:
                    continue
                if not visibles_j and not cachees_j:
                    # Déménager une colonne entière vers une colonne vide ne
                    # change rien à la position.
                    if _valeur(tete) == 13 and not deplace_tout:
                        vides.append(("cc", i, j, nb))
                elif visibles_j:
                    bas = visibles_j[-1]
                    if _valeur(tete) + 1 == _valeur(bas) and _rouge(tete) != _rouge(bas):
                        coup = ("cc", i, j, nb)
                        if k == 0 and cachees:
                            decouvertes.append(coup)
                        else:
                            autres.append(coup)

    # 4. Défausse -> colonne.
    if defausse:
        c = defausse[-1]
        for j, (cachees_j, visibles_j) in enumerate(colonnes):
            if visibles_j:
                bas = visibles_j[-1]
                if _valeur(c) + 1 == _valeur(bas) and _rouge(c) != _rouge(bas):
                    autres.append(("dc", j))
            elif not cachees_j and _valeur(c) == 13:
                vides.append(("dc", j))

    # 5. Redescendre une carte d'une base (rarement utile : on ne le tente que
    #    si une carte disponible peut immédiatement s'y accrocher).
    disponibles = [v[-1] for _, v in colonnes if v]
    if defausse:
        disponibles.append(defausse[-1])
    for r in range(4):
        if bases[r] < 3:
            continue
        carte = r * 13 + bases[r] - 1
        if not any(
            _valeur(d) + 1 == _valeur(carte) and _rouge(d) != _rouge(carte)
            for d in disponibles
        ):
            continue
        for j, (cachees_j, visibles_j) in enumerate(colonnes):
            if visibles_j:
                bas = visibles_j[-1]
                if _valeur(carte) + 1 == _valeur(bas) and _rouge(carte) != _rouge(bas):
                    retours.append(("bc", r, j))
            elif not cachees_j and _valeur(carte) == 13:
                retours.append(("bc", r, j))

    coups = decouvertes + montees + autres + vides
    if pioche or defausse:
        coups.append(("p",))
    coups += retours
    return coups


# --------------------------------------------------------------------------
# Fin de partie « à cartes ouvertes »
# --------------------------------------------------------------------------


def _finir_partie_ouverte(etat: tuple, tirage: int, max_coups: int = 400):
    """Termine une position où plus aucune carte n'est cachée.

    Renvoie la liste des coups menant à la victoire, ou ``None`` si la méthode
    gloutonne échoue (cas résiduels du tirage par trois).
    """
    coups: list[tuple] = []
    vus: set = set()
    for _ in range(max_coups):
        if _gagne(etat):
            return coups
        colonnes, bases, pioche, defausse = etat
        meilleur = None
        for i, (_, visibles) in enumerate(colonnes):
            if visibles:
                c = visibles[-1]
                if bases[c // 13] == _valeur(c) - 1:
                    if meilleur is None or _valeur(c) < meilleur[0]:
                        meilleur = (_valeur(c), ("cb", i))
        if defausse:
            c = defausse[-1]
            if bases[c // 13] == _valeur(c) - 1:
                if meilleur is None or _valeur(c) < meilleur[0]:
                    meilleur = (_valeur(c), ("db",))
        if meilleur is not None:
            coup = meilleur[1]
            vus = set()
        elif pioche or defausse:
            coup = ("p",)
            cle = _cle(etat)
            if cle in vus:  # un tour complet du talon sans progrès
                return None
            vus.add(cle)
        else:
            return None
        coups.append(coup)
        etat = _appliquer_compact(etat, coup, tirage)
    return None


# --------------------------------------------------------------------------
# Analyse complète
# --------------------------------------------------------------------------

GAGNABLE = "gagnable"
PERDUE = "perdue"
INDETERMINE = "indetermine"


@dataclass
class Resultat:
    """Verdict de l'analyse."""

    statut: str
    coups: list[Coup]
    noeuds: int
    duree: float

    @property
    def est_gagnable(self) -> bool:
        return self.statut == GAGNABLE

    def message(self) -> str:
        if self.statut == GAGNABLE:
            return (
                f"La partie est encore gagnable : une solution en {len(self.coups)} "
                f"coups a été trouvée ({self.noeuds} positions explorées en "
                f"{self.duree:.1f} s).\n\nLe bouton « Indice » vous guidera "
                "maintenant coup par coup le long de cette solution."
            )
        if self.statut == PERDUE:
            return (
                "Aucune suite de coups ne mène à la victoire : la partie est "
                f"perdue ({self.noeuds} positions explorées en {self.duree:.1f} s)."
                "\n\nVoulez-vous commencer une nouvelle partie ?"
            )
        return (
            f"Analyse interrompue après {self.noeuds} positions et "
            f"{self.duree:.1f} s sans conclusion : la partie est peut-être "
            "gagnable, mais la recherche est trop longue.\n\nVous pouvez "
            "relancer l'analyse pour explorer davantage."
        )


def analyser(
    partie: Partie,
    max_noeuds: int = MAX_NOEUDS_SOLVEUR,
    max_secondes: float = MAX_SECONDES_SOLVEUR,
    doit_arreter=None,
) -> Resultat:
    """Cherche si la partie est encore gagnable (version synchrone, bloquante).

    Consomme entièrement :func:`_recherche_iter` : pratique pour les tests ou
    un script, mais **à éviter dans l'interface graphique**, où c'est
    :func:`_recherche_iter` elle-même qu'il faut piloter par petits pas (voir
    ``Application.lancer_analyse`` dans :mod:`solitaire.ui`) pour ne jamais
    bloquer la boucle d'événements — et surtout pour ne jamais faire tourner
    la recherche dans un thread séparé : Tk/Xlib n'aiment pas du tout qu'un
    autre thread existe en parallèle du sien, même s'il ne touche à aucun
    widget (plantage XCB « Unknown sequence number », classique sous Linux).

    :param doit_arreter: fonction sans argument renvoyant ``True`` pour
        interrompre la recherche.
    """
    depart = time.monotonic()
    tirage = partie.cartes_par_tirage
    etat = etat_compact(partie)

    if _ouvert(etat):
        solution = _finir_partie_ouverte(etat, tirage)
        duree = time.monotonic() - depart
        if solution is not None:
            return Resultat(GAGNABLE, _convertir(partie, solution), 1, duree)
        return Resultat(PERDUE, [], 1, duree)

    noeuds = 0
    for verdict, donnee, noeuds in _recherche_iter(etat, tirage, max_noeuds, max_secondes, depart):
        if verdict == "progres":
            if doit_arreter is not None and doit_arreter():
                duree = time.monotonic() - depart
                return Resultat(INDETERMINE, [], noeuds, duree)
            continue
        duree = time.monotonic() - depart
        if verdict == "gagnable":
            return Resultat(GAGNABLE, _convertir(partie, donnee), noeuds, duree)
        if verdict == "perdue":
            return Resultat(PERDUE, [], noeuds, duree)
        return Resultat(INDETERMINE, [], noeuds, duree)

    # Position sans aucun coup légal dès le départ : arbre vide, perdue.
    return Resultat(PERDUE, [], noeuds, time.monotonic() - depart)


def _recherche_iter(etat, tirage, max_noeuds, max_secondes, depart):
    """Parcours en profondeur avec table de transposition, sous forme de
    générateur repris pas à pas.

    Cède la main tous les 2048 nœuds avec ``("progres", None, noeuds)`` — le
    point idéal pour qu'un appelant coopératif (boucle d'événements Tk, via
    ``after()``) rende la main, vérifie une éventuelle annulation, puis
    reprenne l'itération avec ``next()``. Se termine par l'un de :

    * ``("gagnable", coups_compacts, noeuds)``
    * ``("perdue", None, noeuds)`` — arbre entièrement exploré ;
    * ``("indetermine", None, noeuds)`` — budget épuisé.
    """
    visites = {hash(_cle(etat))}  # on ne stocke que les empreintes : moins de mémoire
    pile = [(etat, iter(_coups_compacts(etat, tirage)))]
    chemin: list[tuple] = []
    noeuds = 0

    while pile:
        noeuds += 1
        if noeuds % 2048 == 0:
            if noeuds > max_noeuds or time.monotonic() - depart > max_secondes:
                yield ("indetermine", None, noeuds)
                return
            yield ("progres", None, noeuds)

        courant, coups = pile[-1]
        coup = next(coups, None)
        if coup is None:
            pile.pop()
            if chemin:
                chemin.pop()
            continue

        suivant = _appliquer_compact(courant, coup, tirage)
        empreinte = hash(_cle(suivant))
        if empreinte in visites:
            continue
        visites.add(empreinte)

        if _gagne(suivant):
            yield ("gagnable", chemin + [coup], noeuds)
            return
        if _ouvert(suivant):
            fin = _finir_partie_ouverte(suivant, tirage)
            if fin is not None:
                yield ("gagnable", chemin + [coup] + fin, noeuds)
                return

        chemin.append(coup)
        pile.append((suivant, iter(_coups_compacts(suivant, tirage))))

    yield ("perdue", None, noeuds)


def _convertir(partie: Partie, coups_compacts: list[tuple]) -> list[Coup]:
    """Rejoue la solution sur une copie de la partie pour produire des
    :class:`Coup` complets (avec la carte concernée)."""
    copie = partie.copie()
    resultat: list[Coup] = []
    for compact in coups_compacts:
        coup = _vers_coup(copie, compact)
        resultat.append(coup)
        if not copie.appliquer(coup):  # pragma: no cover - sécurité
            raise RuntimeError(f"Coup incohérent produit par le solveur : {coup}")
    return resultat


def _vers_coup(partie: Partie, compact: tuple) -> Coup:
    type_coup = compact[0]
    if type_coup == "p":
        return Coup("pioche", -1, "defausse")
    if type_coup == "cb":
        i = compact[1]
        carte = partie.colonnes[i].visibles[-1]
        return Coup("colonne", i, "base", carte.rang_symbole, 1, carte)
    if type_coup == "cc":
        _, i, j, nb = compact
        carte = partie.colonnes[i].visibles[-nb]
        return Coup("colonne", i, "colonne", j, nb, carte)
    if type_coup == "db":
        carte = partie.carte_defausse
        return Coup("defausse", -1, "base", carte.rang_symbole, 1, carte)
    if type_coup == "dc":
        carte = partie.carte_defausse
        return Coup("defausse", -1, "colonne", compact[1], 1, carte)
    if type_coup == "bc":
        _, r, j = compact
        return Coup("base", r, "colonne", j, 1, partie.carte_base(r))
    raise ValueError(f"Coup inconnu : {compact}")


# --------------------------------------------------------------------------
# Indice heuristique
# --------------------------------------------------------------------------


def meilleur_coup(partie: Partie) -> Coup | None:
    """Renvoie le coup jugé le plus utile, ou ``None`` s'il n'y en a aucun."""
    coups = partie.coups_legaux(inclure_pioche=True)
    if not coups:
        return None
    return max(coups, key=lambda coup: _note(partie, coup))


def _note(partie: Partie, coup: Coup) -> tuple:
    """Note d'un coup ; plus la note est grande, plus le coup est conseillé."""
    if coup.est_pioche:
        return (0, 0, 0)

    carte = coup.carte
    assert carte is not None

    if coup.destination == "base":
        # Monter est presque toujours bon, et absolument prioritaire quand
        # c'est « sûr » (la carte ne peut plus servir dans le tableau).
        sur = _est_sur(_code(carte), tuple(len(b) for b in partie.bases))
        return (60 if sur else 40, 13 - carte.valeur, 0)

    if coup.origine == "base":
        return (-10, 0, 0)  # redescendre une carte : en dernier recours

    if coup.origine == "colonne":
        colonne = partie.colonnes[coup.i_origine]
        libere_carte = coup.nb == len(colonne.visibles) and bool(colonne.cachees)
        vide_colonne = coup.nb == len(colonne.visibles) and not colonne.cachees
        if libere_carte:
            # Découvrir une carte cachée : le meilleur coup du tableau.
            return (50, len(colonne.cachees), carte.valeur)
        if vide_colonne:
            return (-5, 0, 0)  # simple déménagement, sans intérêt
        return (20, 0, carte.valeur)

    # Origine : défausse
    if partie.colonnes[coup.i_destination].est_vide:
        return (25, 0, carte.valeur)
    return (30, 0, carte.valeur)



def solution_partie_ouverte(partie: Partie) -> list[Coup] | None:
    """Suite de coups terminant une partie dont toutes les cartes sont
    visibles, ou ``None`` si la position n'est pas ouverte."""
    etat = etat_compact(partie)
    if not _ouvert(etat):
        return None
    coups = _finir_partie_ouverte(etat, partie.cartes_par_tirage)
    if coups is None:
        return None
    return _convertir(partie, coups)