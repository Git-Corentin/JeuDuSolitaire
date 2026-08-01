"""Réglages de l'application et fenêtre de paramètres.

Les réglages sont regroupés dans un objet :class:`Reglages` unique, que
l'interface consulte à chaque usage : modifier une valeur prend donc effet
immédiatement, sans avoir à relancer la partie.
"""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from tkinter import colorchooser

from . import config


@dataclass
class Reglages:
    """Tous les réglages modifiables par le joueur."""

    # Apparence
    couleur_fond: str = config.COULEUR_FOND_DEFAUT
    couleur_texte: str = "white"
    couleur_surlignage: str = config.COULEUR_SURLIGNAGE_DEFAUT
    couleur_destination: str = config.COULEUR_DESTINATION_DEFAUT

    # Solveur
    duree_analyse: float = config.MAX_SECONDES_SOLVEUR
    noeuds_analyse: int = config.MAX_NOEUDS_SOLVEUR

    # Confort de jeu
    ms_par_coup_finition: int = config.MS_PAR_COUP_FINITION
    glisser_deposer: bool = True
    eviter_retours_indice: bool = True


class FenetreParametres(tk.Toplevel):
    """Boîte de dialogue de configuration.

    Chaque modification est appliquée immédiatement via ``au_changement``, ce
    qui permet de voir l'effet des couleurs sans fermer la fenêtre.
    """

    def __init__(self, parent: tk.Misc, reglages: Reglages, au_changement) -> None:
        super().__init__(parent)
        self.title("Paramètres")
        self.reglages = reglages
        self.au_changement = au_changement
        self.transient(parent)
        self.resizable(False, False)

        corps = tk.Frame(self, padx=16, pady=12)
        corps.pack(fill=tk.BOTH, expand=True)

        self._section(corps, "Apparence")
        self._ligne_couleur(corps, "Couleur du fond", "couleur_fond")
        self._ligne_couleur(corps, "Surlignage de l'indice", "couleur_surlignage")
        self._ligne_couleur(corps, "Destination de l'indice", "couleur_destination")

        self._section(corps, "Solveur")
        self.var_duree = tk.DoubleVar(value=reglages.duree_analyse)
        self._ligne_nombre(
            corps,
            "Durée maximale d'une analyse (s)",
            self.var_duree,
            de=5,
            a=600,
            pas=5,
            attribut="duree_analyse",
            conversion=float,
        )
        self.var_noeuds = tk.IntVar(value=reglages.noeuds_analyse // 1000)
        self._ligne_nombre(
            corps,
            "Positions explorées au maximum (en milliers)",
            self.var_noeuds,
            de=50,
            a=50_000,
            pas=250,
            attribut="noeuds_analyse",
            conversion=lambda v: int(v) * 1000,
        )
        tk.Label(
            corps,
            text=(
                "Relancer une analyse non concluante reprend la recherche\n"
                "là où elle s'était arrêtée, avec un budget doublé."
            ),
            justify="left",
            fg="#555555",
        ).pack(anchor="w", pady=(0, 6))

        self._section(corps, "Confort de jeu")
        self.var_glisser = tk.BooleanVar(value=reglages.glisser_deposer)
        tk.Checkbutton(
            corps,
            text="Activer le glisser-déposer (le clic-clic reste possible)",
            variable=self.var_glisser,
            command=lambda: self._definir("glisser_deposer", self.var_glisser.get()),
            anchor="w",
        ).pack(fill=tk.X)
        self.var_eviter = tk.BooleanVar(value=reglages.eviter_retours_indice)
        tk.Checkbutton(
            corps,
            text="Interdire à l'indice de revenir sur une position déjà vue",
            variable=self.var_eviter,
            command=lambda: self._definir(
                "eviter_retours_indice", self.var_eviter.get()
            ),
            anchor="w",
        ).pack(fill=tk.X)
        self.var_vitesse = tk.IntVar(value=reglages.ms_par_coup_finition)
        self._ligne_nombre(
            corps,
            "Finition automatique (ms par coup)",
            self.var_vitesse,
            de=5,
            a=500,
            pas=5,
            attribut="ms_par_coup_finition",
            conversion=int,
        )

        tk.Button(corps, text="Fermer", command=self.destroy).pack(pady=(12, 0))

    # -- Constructeurs de lignes -------------------------------------------

    def _section(self, parent: tk.Misc, titre: str) -> None:
        tk.Label(parent, text=titre, font="TkDefaultFont 10 bold").pack(
            anchor="w", pady=(10, 4)
        )

    def _ligne_couleur(self, parent: tk.Misc, libelle: str, attribut: str) -> None:
        ligne = tk.Frame(parent)
        ligne.pack(fill=tk.X, pady=2)
        tk.Label(ligne, text=libelle, width=34, anchor="w").pack(side=tk.LEFT)
        apercu = tk.Button(ligne, width=6, bg=getattr(self.reglages, attribut))

        def choisir() -> None:
            couleur = colorchooser.askcolor(
                getattr(self.reglages, attribut), title=libelle, parent=self
            )
            if couleur[1] is None:
                return
            apercu.configure(bg=couleur[1])
            self._definir(attribut, couleur[1], rvb=couleur[0])

        apercu.configure(command=choisir)
        apercu.pack(side=tk.LEFT)

    def _ligne_nombre(
        self, parent, libelle, variable, de, a, pas, attribut, conversion
    ) -> None:
        ligne = tk.Frame(parent)
        ligne.pack(fill=tk.X, pady=2)
        tk.Label(ligne, text=libelle, width=34, anchor="w").pack(side=tk.LEFT)
        tk.Spinbox(
            ligne,
            from_=de,
            to=a,
            increment=pas,
            textvariable=variable,
            width=8,
            command=lambda: self._definir(attribut, conversion(variable.get())),
        ).pack(side=tk.LEFT)
        variable.trace_add(
            "write", lambda *_: self._definir_sur(attribut, variable, conversion)
        )

    # -- Application des changements ---------------------------------------

    def _definir_sur(self, attribut, variable, conversion) -> None:
        try:
            valeur = conversion(variable.get())
        except (tk.TclError, ValueError):
            return  # champ en cours de saisie, incomplet
        self._definir(attribut, valeur)

    def _definir(self, attribut: str, valeur, rvb=None) -> None:
        setattr(self.reglages, attribut, valeur)
        self.au_changement(attribut, rvb)
