"""Interface graphique (tkinter) du solitaire.

L'interface ne contient aucune règle du jeu : elle traduit les clics en
:class:`~solitaire.partie.Coup` que le modèle valide et applique, puis redessine
le plateau à partir de l'état du modèle. Cette séparation supprime toute la
comptabilité manuelle des objets du canevas (et les désynchronisations qui
allaient avec).

Commandes :

* clic gauche : prendre une (ou plusieurs) carte(s), puis clic gauche sur la
  destination pour la poser ;
* clic droit ou ``Échap`` : reposer les cartes prises ;
* double-clic : envoyer automatiquement la carte sur une base ou une colonne ;
* ``Ctrl+Z`` : annuler le dernier coup ; ``H`` : indice ; ``A`` : analyse ;
* ``Espace`` : piocher ; ``N`` : nouvelle partie.
"""

from __future__ import annotations

import time
import tkinter as tk
from colorsys import rgb_to_hls
from tkinter import TclError, colorchooser, messagebox

from . import config, solveur
from .assets import Ressources, choisir_echelle
from .partie import Coup, Partie

COULEUR_SURLIGNAGE = "#ffd400"
COULEUR_DESTINATION = "#ff5252"


def maximiser(fenetre: tk.Tk) -> None:
    """Agrandit la fenêtre, quel que soit le système.

    ``wm state zoomed`` n'existe que sous Windows (et sur certains macOS) ;
    la plupart des gestionnaires de fenêtres Linux utilisent l'attribut
    ``-zoomed``, et certains ne proposent rien du tout — d'où le repli sur une
    géométrie explicite.
    """
    for tentative in (
        lambda: fenetre.state("zoomed"),
        lambda: fenetre.attributes("-zoomed", True),
    ):
        try:
            tentative()
            return
        except TclError:
            continue
    fenetre.geometry(
        f"{fenetre.winfo_screenwidth()}x{fenetre.winfo_screenheight()}+0+0"
    )


class Application:
    """Fenêtre principale du jeu."""

    def __init__(
        self,
        tirage: int = 1,
        graine: int | None = None,
        echelle: tuple[int, int] | None = None,
        dossier_images: str | None = None,
    ) -> None:
        self.fen = tk.Tk()
        self.fen.title("Solitaire")
        maximiser(self.fen)
        self.fen.protocol("WM_DELETE_WINDOW", self.quitter)

        largeur = self.fen.winfo_screenwidth()
        hauteur = self.fen.winfo_screenheight()
        if echelle is None:
            echelle = choisir_echelle(largeur - 20, hauteur - 90)
        self.res = Ressources(dossier_images, echelle)
        self.res.centrer(largeur, hauteur)

        try:  # icône de fenêtre (facultative)
            self.fen.iconphoto(True, self.res.dos)
        except TclError:  # pragma: no cover
            pass

        self.couleur_fond = config.COULEUR_FOND_DEFAUT
        self.couleur_texte = "white"

        self.partie: Partie | None = None
        self.graine = graine
        self.selection: dict | None = None
        self.chrono_secondes = 0
        self.chrono_actif = False
        self.indice_actif = False
        self.coup_indice: Coup | None = None
        self.solution: list[Coup] = []
        self._gen_analyse = None  # générateur de recherche en cours, ou None
        self._copie_analyse: Partie | None = None
        self._depart_analyse = 0.0
        self._coups_au_lancement_analyse = 0
        self.fin_proposee = False

        self.var_tirage = tk.IntVar(value=tirage)

        self._construire_interface()
        self._appliquer_couleurs()
        self.redessiner()
        self._tic()

    # ------------------------------------------------------------------
    # Construction de l'interface
    # ------------------------------------------------------------------

    def _construire_interface(self) -> None:
        self.can = tk.Canvas(
            self.fen,
            bg=self.couleur_fond,
            highlightthickness=0,
            width=self.fen.winfo_screenwidth(),
            height=self.fen.winfo_screenheight(),
        )
        self.can.pack(fill=tk.BOTH, expand=True)

        px = self.res.px
        police = f"Cambria {max(10, px(30))}"
        police_bouton = f"Cambria {max(8, px(20))}"

        self.label_temps = tk.Label(self.can, text="Temps : 0:00:00", font=police)
        self._placer(self.label_temps, 150, 50)
        self.label_score = tk.Label(self.can, text="Score : 0", font=police)
        self._placer(self.label_score, 150, 120)

        self.bouton_jouer = tk.Button(
            self.can,
            image=self.res.jouer,
            borderwidth=0,
            command=self.nouvelle_partie,
        )
        self._placer(self.bouton_jouer, 370, config.Y_BOUTON_JOUER, "center")

        self.radio_une = tk.Radiobutton(
            self.can,
            image=self.res.une_carte_off,
            selectimage=self.res.une_carte,
            variable=self.var_tirage,
            value=1,
            indicatoron=0,
            borderwidth=0,
        )
        self._placer(self.radio_une, 255, config.Y_RADIOS, "center")
        self.radio_trois = tk.Radiobutton(
            self.can,
            image=self.res.trois_cartes_off,
            selectimage=self.res.trois_cartes,
            variable=self.var_tirage,
            value=3,
            indicatoron=0,
            borderwidth=0,
        )
        self._placer(self.radio_trois, 485, config.Y_RADIOS, "center")

        self.bouton_parametre = tk.Button(
            self.can, image=self.res.parametre, borderwidth=0, command=self.choisir_fond
        )
        self._placer(self.bouton_parametre, 255, config.Y_BOUTONS_OUTILS, "center")
        self.bouton_indice = tk.Button(
            self.can,
            image=self.res.indice_inactif,
            borderwidth=0,
            command=self.basculer_indice,
        )
        self._placer(self.bouton_indice, 485, config.Y_BOUTONS_OUTILS, "center")

        self.bouton_analyse = tk.Button(
            self.can,
            text="Analyser la partie  (A)",
            font=police_bouton,
            borderwidth=0,
            command=self.lancer_analyse,
        )
        self._placer(self.bouton_analyse, 370, config.Y_BOUTON_ANALYSE, "center")
        self.bouton_annuler = tk.Button(
            self.can,
            text="Annuler le coup  (Ctrl+Z)",
            font=police_bouton,
            borderwidth=0,
            command=self.annuler_coup,
        )
        self._placer(self.bouton_annuler, 370, config.Y_BOUTON_ANNULER, "center")

        self.label_message = tk.Label(
            self.can,
            text="",
            font=f"Cambria {max(8, px(17))}",
            wraplength=px(660),
            justify="center",
        )
        self._placer(self.label_message, 370, config.Y_MESSAGE, "center")

        self.can.bind("<Button-1>", self.clic_gauche)
        self.can.bind("<Double-Button-1>", self.double_clic)
        self.can.bind("<Button-3>", lambda _e: self.annuler_selection())
        self.can.bind("<Motion>", self.deplacer_selection)
        self.fen.bind("<Escape>", self.echap)
        self.fen.bind("<Control-z>", lambda _e: self.annuler_coup())
        self.fen.bind("<n>", lambda _e: self.nouvelle_partie())
        self.fen.bind("<h>", lambda _e: self.basculer_indice())
        self.fen.bind("<a>", lambda _e: self.lancer_analyse())
        self.fen.bind("<space>", lambda _e: self.piocher())

    def _placer(self, widget, x: float, y: float, ancrage: str = "nw") -> None:
        """Place un widget aux coordonnées de référence (x, y)."""
        ecran_x, ecran_y = self.res.point((x, y))
        widget.place(x=ecran_x, y=ecran_y, anchor=ancrage)

    def _widgets_colores(self) -> list[tk.Widget]:
        return [
            self.bouton_jouer,
            self.bouton_parametre,
            self.bouton_indice,
            self.bouton_analyse,
            self.bouton_annuler,
            self.radio_une,
            self.radio_trois,
        ]

    def _appliquer_couleurs(self) -> None:
        self.can.configure(bg=self.couleur_fond)
        for widget in (self.label_temps, self.label_score, self.label_message):
            widget.configure(bg=self.couleur_fond, fg=self.couleur_texte)
        for widget in self._widgets_colores():
            widget.configure(bg=self.couleur_fond, activebackground=self.couleur_fond)
            if isinstance(widget, tk.Radiobutton):
                widget.configure(selectcolor=self.couleur_fond)
            if isinstance(widget, tk.Button) and widget.cget("text"):
                widget.configure(
                    fg=self.couleur_texte, activeforeground=self.couleur_texte
                )

    # ------------------------------------------------------------------
    # Cycle de la partie
    # ------------------------------------------------------------------

    def nouvelle_partie(self, confirmer: bool = True) -> None:
        if (
            confirmer
            and self.partie is not None
            and self.partie.nb_coups > 0
            and not self.partie.est_gagnee
            and not messagebox.askyesno(
                "Nouvelle partie", "Abandonner la partie en cours ?"
            )
        ):
            return
        self.arreter_analyse()
        self.partie = Partie(self.var_tirage.get(), graine=self.graine)
        self.graine = None  # la graine ne sert qu'à la première donne
        self.selection = None
        self.solution = []
        self.coup_indice = None
        self.indice_actif = False
        self.fin_proposee = False
        self.bouton_indice.configure(image=self.res.indice_inactif)
        self.chrono_secondes = 0
        self.chrono_actif = True
        self.message("")
        self.redessiner()

    def quitter(self) -> None:
        self.arreter_analyse()
        self.chrono_actif = False
        self.fen.destroy()

    def lancer(self) -> None:
        self.fen.mainloop()

    # ------------------------------------------------------------------
    # Chronomètre et affichage textuel
    # ------------------------------------------------------------------

    def _tic(self) -> None:
        if self.chrono_actif and self.partie is not None:
            self.chrono_secondes += 1
            heures, reste = divmod(self.chrono_secondes, 3600)
            minutes, secondes = divmod(reste, 60)
            self.label_temps.configure(
                text=f"Temps : {heures}:{minutes:02d}:{secondes:02d}"
            )
        self.fen.after(1000, self._tic)

    def message(self, texte: str) -> None:
        self.label_message.configure(text=texte)

    def _maj_score(self) -> None:
        score = self.partie.score if self.partie else 0
        self.label_score.configure(text=f"Score : {score}")

    # ------------------------------------------------------------------
    # Géométrie
    # ------------------------------------------------------------------

    def point_colonne(self, i: int) -> tuple[int, int]:
        """Coordonnées écran de la première carte de la colonne ``i``."""
        return self.res.point(
            (config.X_PLATEAU + i * config.ECART_COLONNES, config.Y_COLONNES)
        )

    def positions_colonne(self, i: int) -> list[tuple[int, int]]:
        """Coordonnées (centre) de chaque carte de la colonne ``i``."""
        colonne = self.partie.colonnes[i]
        x, y = self.point_colonne(i)
        positions = []
        for _ in colonne.cachees:
            positions.append((x, y))
            y += self.res.px(config.ECART_CACHEE)
        for _ in colonne.visibles:
            positions.append((x, y))
            y += self.res.px(config.ECART_VISIBLE)
        return positions

    def position_libre_colonne(self, i: int) -> tuple[int, int]:
        """Coordonnées de la prochaine carte posée sur la colonne ``i``."""
        colonne = self.partie.colonnes[i]
        x, y = self.point_colonne(i)
        y += self.res.px(config.ECART_CACHEE) * len(colonne.cachees)
        y += self.res.px(config.ECART_VISIBLE) * len(colonne.visibles)
        return x, y

    def _dans_carte(self, x: int, y: int, centre: tuple[int, int]) -> bool:
        demi_l = self.res.largeur_carte / 2
        demi_h = self.res.hauteur_carte / 2
        return (
            centre[0] - demi_l <= x <= centre[0] + demi_l
            and centre[1] - demi_h <= y <= centre[1] + demi_h
        )

    def zone(self, x: int, y: int):
        """Zone cliquée : ``("pioche", -1, -1)``, ``("defausse", -1, -1)``,
        ``("base", rang, -1)``, ``("colonne", i, indice_visible)`` ou ``None``.

        ``indice_visible`` vaut ``-1`` si le clic porte sur une carte cachée ou
        sur une colonne vide.
        """
        if self.partie is None:
            return None
        if self._dans_carte(x, y, self.res.point(config.COORD_PIOCHE)):
            return ("pioche", -1, -1)
        for coord in config.COORDS_DEFAUSSE:
            if self._dans_carte(x, y, self.res.point(coord)):
                return ("defausse", -1, -1)
        for rang, coord in enumerate(config.COORDS_BASES):
            if self._dans_carte(x, y, self.res.point(coord)):
                return ("base", rang, -1)
        for i in range(7):
            positions = self.positions_colonne(i)
            if not positions:
                if self._dans_carte(
                    x, y, (self.position_libre_colonne(i))
                ):
                    return ("colonne", i, -1)
                continue
            for indice in range(len(positions) - 1, -1, -1):
                if self._dans_carte(x, y, positions[indice]):
                    nb_cachees = len(self.partie.colonnes[i].cachees)
                    return ("colonne", i, max(-1, indice - nb_cachees))
        return None

    # ------------------------------------------------------------------
    # Dessin
    # ------------------------------------------------------------------

    def redessiner(self) -> None:
        self.can.delete("plateau")
        self._dessiner_menu()
        if self.partie is None:
            self._dessiner_plateau_vide()
            self.message(
                "Choisissez le mode de tirage puis cliquez sur JOUER "
                "(ou appuyez sur N)."
            )
            self._maj_score()
            self.bouton_annuler.configure(state=tk.DISABLED)
            return
        self._dessiner_pioche()
        self._dessiner_defausse()
        self._dessiner_bases()
        self._dessiner_colonnes()
        self._dessiner_indice()
        self._maj_score()
        self.bouton_annuler.configure(
            state=tk.NORMAL if self.partie.peut_annuler else tk.DISABLED
        )

    def _image(self, coord, image, **kwargs):
        self.can.create_image(coord, image=image, tags=("plateau",), **kwargs)

    def _dessiner_menu(self) -> None:
        self._image(self.res.point(config.COORD_LOGO), self.res.logo)

    def _dessiner_plateau_vide(self) -> None:
        """Emplacements vides affichés avant le début de la partie."""
        self._image(self.res.point(config.COORD_PIOCHE), self.res.vide)
        for rang, coord in enumerate(config.COORDS_BASES):
            self._image(self.res.point(coord), self.res.bases[rang])
        for i in range(7):
            self._image(self.point_colonne(i), self.res.vide)

    def _dessiner_pioche(self) -> None:
        coord = self.res.point(config.COORD_PIOCHE)
        if self.partie.pioche:
            self._image(coord, self.res.dos)
        elif self.partie.defausse:
            self._image(coord, self.res.retourne)
        else:
            self._image(coord, self.res.vide)

    def _dessiner_defausse(self) -> None:
        defausse = list(self.partie.defausse)
        if self.selection and self.selection["origine"] == "defausse":
            defausse = defausse[:-1]
        nb = min(self.partie.cartes_par_tirage, len(defausse), 3)
        for k, carte in enumerate(defausse[len(defausse) - nb:] if nb else []):
            self._image(
                self.res.point(config.COORDS_DEFAUSSE[k]), self.res.cartes[carte.nom]
            )

    def _dessiner_bases(self) -> None:
        for rang, coord in enumerate(config.COORDS_BASES):
            base = list(self.partie.bases[rang])
            if (
                self.selection
                and self.selection["origine"] == "base"
                and self.selection["i"] == rang
            ):
                base = base[:-1]
            point = self.res.point(coord)
            if base:
                self._image(point, self.res.cartes[base[-1].nom])
            else:
                self._image(point, self.res.bases[rang])

    def _dessiner_colonnes(self) -> None:
        for i in range(7):
            colonne = self.partie.colonnes[i]
            visibles = list(colonne.visibles)
            if (
                self.selection
                and self.selection["origine"] == "colonne"
                and self.selection["i"] == i
            ):
                visibles = visibles[: len(visibles) - len(self.selection["cartes"])]
            positions = self.positions_colonne(i)
            if not colonne.cachees and not visibles:
                self._image(self.point_colonne(i), self.res.vide)
                continue
            for k, _ in enumerate(colonne.cachees):
                self._image(positions[k], self.res.dos)
            for k, carte in enumerate(visibles):
                self._image(
                    positions[len(colonne.cachees) + k], self.res.cartes[carte.nom]
                )

    def _cadre(self, centre, hauteur_supplementaire: int, couleur: str, tirets=None):
        demi_l = self.res.largeur_carte / 2 + 3
        demi_h = self.res.hauteur_carte / 2 + 3
        self.can.create_rectangle(
            centre[0] - demi_l,
            centre[1] - demi_h,
            centre[0] + demi_l,
            centre[1] + demi_h + hauteur_supplementaire,
            outline=couleur,
            width=4,
            dash=tirets,
            tags=("plateau",),
        )

    def _dessiner_indice(self) -> None:
        coup = self.coup_indice
        if not self.indice_actif or coup is None:
            return
        # Origine
        if coup.est_pioche:
            self._cadre(self.res.point(config.COORD_PIOCHE), 0, COULEUR_SURLIGNAGE)
            return
        if coup.origine == "colonne":
            positions = self.positions_colonne(coup.i_origine)
            depart = positions[len(positions) - coup.nb]
            supplement = self.res.px(config.ECART_VISIBLE) * (coup.nb - 1)
            self._cadre(depart, supplement, COULEUR_SURLIGNAGE)
        elif coup.origine == "defausse":
            nb = min(self.partie.cartes_par_tirage, len(self.partie.defausse), 3)
            self._cadre(
                self.res.point(config.COORDS_DEFAUSSE[nb - 1]), 0, COULEUR_SURLIGNAGE
            )
        else:
            self._cadre(
                self.res.point(config.COORDS_BASES[coup.i_origine]),
                0,
                COULEUR_SURLIGNAGE,
            )
        # Destination
        if coup.destination == "base":
            cible = self.res.point(config.COORDS_BASES[coup.i_destination])
            if not self.partie.bases[coup.i_destination]:
                self._image(cible, self.res.repere(1))
        else:
            cible = self.position_libre_colonne(coup.i_destination)
            if self.partie.colonnes[coup.i_destination].est_vide:
                self._image(cible, self.res.repere(1))
        self._cadre(cible, 0, COULEUR_DESTINATION, tirets=(6, 4))

    def _dessiner_selection(self, x: int, y: int) -> None:
        """Fait suivre le curseur aux cartes tenues en main."""
        if not self.selection:
            self.can.delete("main_joueur")
            return
        ecart = self.res.px(config.ECART_VISIBLE)
        objets = self.selection.get("objets")
        if not objets:
            objets = [
                self.can.create_image(
                    x,
                    y + k * ecart,
                    image=self.res.cartes[carte.nom],
                    tags=("main_joueur",),
                )
                for k, carte in enumerate(self.selection["cartes"])
            ]
            self.selection["objets"] = objets
        else:
            for k, objet in enumerate(objets):
                self.can.coords(objet, x, y + k * ecart)
        self.can.tag_raise("main_joueur")

    # ------------------------------------------------------------------
    # Interactions
    # ------------------------------------------------------------------

    def clic_gauche(self, event) -> None:
        if self.partie is None:
            return
        zone = self.zone(event.x, event.y)
        if self.selection is None:
            self._prendre(zone, event)
        else:
            self._poser(zone, event)

    def _prendre(self, zone, event) -> None:
        if zone is None:
            return
        type_zone, i, indice = zone
        if type_zone == "pioche":
            self.piocher()
            return
        cartes: list = []
        if type_zone == "defausse":
            carte = self.partie.carte_defausse
            if carte is None:
                return
            cartes = [carte]
        elif type_zone == "base":
            carte = self.partie.carte_base(i)
            if carte is None:
                return
            cartes = [carte]
        elif type_zone == "colonne":
            if indice < 0:
                return
            cartes = self.partie.colonnes[i].visibles[indice:]
            if not cartes:
                return
        self.selection = {"origine": type_zone, "i": i, "cartes": cartes, "objets": []}
        self.redessiner()
        self._dessiner_selection(event.x, event.y)

    def _poser(self, zone, event) -> None:
        if zone is None:
            self.annuler_selection()
            return
        type_zone, i, _ = zone
        selection = self.selection
        if type_zone == selection["origine"] and (
            type_zone == "defausse" or i == selection["i"]
        ):
            self.annuler_selection()
            return
        coup = self._coup_vers(type_zone, i)
        if coup is None or not self.jouer(coup):
            self.message("Ce déplacement n'est pas autorisé.")
            self._dessiner_selection(event.x, event.y)

    def _coup_vers(self, type_zone: str, i: int) -> Coup | None:
        selection = self.selection
        if selection is None or type_zone not in ("colonne", "base"):
            return None
        carte = selection["cartes"][0]
        destination = "base" if type_zone == "base" else "colonne"
        i_destination = carte.rang_symbole if destination == "base" else i
        if destination == "base" and i != carte.rang_symbole:
            return None
        return Coup(
            selection["origine"],
            selection["i"],
            destination,
            i_destination,
            len(selection["cartes"]),
            carte,
        )

    def deplacer_selection(self, event) -> None:
        if self.selection:
            self._dessiner_selection(event.x, event.y)

    def annuler_selection(self) -> None:
        if self.selection:
            self.selection = None
            self.can.delete("main_joueur")
            self.redessiner()

    def echap(self, _event=None) -> None:
        if self._gen_analyse is not None:
            self.arreter_analyse()
            self.message("Analyse interrompue.")
            return
        self.annuler_selection()

    def double_clic(self, event) -> None:
        if self.partie is None:
            return
        if self.selection is None:
            zone = self.zone(event.x, event.y)
            if zone and zone[0] == "pioche":
                self.piocher()
            return
        carte = self.selection["cartes"][0]
        # 1. Vers une base, si une seule carte est prise.
        if len(self.selection["cartes"]) == 1:
            coup = self._coup_vers("base", carte.rang_symbole)
            if coup and self.jouer(coup):
                return
        # 2. Sinon vers la première colonne compatible.
        for j in range(7):
            if j == self.selection["i"] and self.selection["origine"] == "colonne":
                continue
            coup = self._coup_vers("colonne", j)
            if coup and self.partie.coup_valide(coup) and self.jouer(coup):
                return
        self.annuler_selection()

    def piocher(self) -> None:
        if self.partie is None:
            return
        self.annuler_selection()
        self.jouer(Coup("pioche", -1, "defausse"))

    def annuler_coup(self) -> None:
        if self.partie is None:
            return
        self.annuler_selection()
        if self.partie.annuler():
            self.solution = []
            self.message("Coup annulé.")
            self._maj_indice()
            self.redessiner()

    # ------------------------------------------------------------------
    # Application d'un coup
    # ------------------------------------------------------------------

    def jouer(self, coup: Coup) -> bool:
        """Joue un coup et met à jour l'affichage. Renvoie ``False`` si le coup
        est refusé par les règles."""
        if self.partie is None or not self.partie.appliquer(coup):
            return False
        self.selection = None
        self.can.delete("main_joueur")
        if self.solution and self.solution[0] == coup:
            self.solution.pop(0)
        elif self.solution:
            self.solution = []
        self._maj_indice()
        self.message("")
        self.redessiner()
        self._verifier_fin()
        return True

    def _verifier_fin(self) -> None:
        partie = self.partie
        if partie is None:
            return
        if partie.est_gagnee:
            self.chrono_actif = False
            self.can.update_idletasks()
            if messagebox.askyesno(
                "Victoire !",
                f"Bravo, vous avez gagné avec {partie.score} points !\n\n"
                "Voulez-vous rejouer ?",
            ):
                self.nouvelle_partie(confirmer=False)
            return
        if partie.est_ouverte and not self.fin_proposee:
            self.fin_proposee = True
            if messagebox.askyesno(
                "Fin de partie",
                "Toutes les cartes sont retournées : la victoire est assurée.\n\n"
                "Voulez-vous terminer automatiquement ?",
            ):
                self.terminer_automatiquement()
            return
        if not partie.coups_legaux():
            self.chrono_actif = False
            messagebox.showinfo(
                "Partie bloquée",
                "Plus aucun coup n'est possible : la partie est perdue.",
            )

    def terminer_automatiquement(self) -> None:
        coups = solveur.solution_partie_ouverte(self.partie)
        if not coups:
            self.message("La finition automatique n'a pas abouti.")
            return

        def suivant(reste: list[Coup]) -> None:
            if not reste or self.partie is None:
                self._verifier_fin()
                return
            self.partie.appliquer(reste[0])
            self.redessiner()
            self.fen.after(40, suivant, reste[1:])

        suivant(coups)

    # ------------------------------------------------------------------
    # Aide : indice et analyse
    # ------------------------------------------------------------------

    def basculer_indice(self) -> None:
        if self.partie is None:
            return
        if self.indice_actif:
            self.indice_actif = False
            self.coup_indice = None
            self.bouton_indice.configure(image=self.res.indice_inactif)
            self.message("")
            self.redessiner()
            return
        self.annuler_selection()
        self.indice_actif = True
        self.bouton_indice.configure(image=self.res.indice_actif)
        self._maj_indice()
        if self.coup_indice is None:
            self.indice_actif = False
            self.bouton_indice.configure(image=self.res.indice_inactif)
            if messagebox.askyesno(
                "Indice",
                "Aucun coup n'est possible.\n\nVoulez-vous commencer une "
                "nouvelle partie ?",
            ):
                self.nouvelle_partie(confirmer=False)
            return
        self.redessiner()

    def _maj_indice(self) -> None:
        """Recalcule le coup conseillé (en suivant la solution si elle existe)."""
        if not self.indice_actif or self.partie is None:
            self.coup_indice = None
            return
        coup = None
        if self.solution and self.partie.coup_valide(self.solution[0]):
            coup = self.solution[0]
            suffixe = f"  (solution : {len(self.solution)} coups restants)"
        else:
            coup = solveur.meilleur_coup(self.partie)
            suffixe = ""
        self.coup_indice = coup
        self.message(coup.description() + suffixe if coup else "")

    def lancer_analyse(self) -> None:
        """Démarre l'analyse de solvabilité.

        La recherche est un générateur (:func:`solveur._recherche_iter`)
        repris par petits pas via ``fen.after()`` : tout se passe dans le
        thread principal. Un vrai thread romprait la boucle d'événements Tk
        (plantage XCB « Unknown sequence number », un classique de
        Tk/Xlib sous Linux dès qu'un second thread existe, même s'il ne
        touche à aucun widget).
        """
        if self.partie is None or self._gen_analyse is not None:
            return
        self.annuler_selection()
        depart = time.monotonic()
        copie = self.partie.copie()
        etat = solveur.etat_compact(copie)

        if solveur._ouvert(etat):  # partie déjà gagnée d'avance : instantané
            solution = solveur._finir_partie_ouverte(etat, copie.cartes_par_tirage)
            resultat = solveur.Resultat(
                solveur.GAGNABLE if solution is not None else solveur.PERDUE,
                solveur._convertir(copie, solution) if solution is not None else [],
                1,
                time.monotonic() - depart,
            )
            self._appliquer_resultat_analyse(resultat, self.partie.nb_coups)
            return

        self._gen_analyse = solveur._recherche_iter(
            etat,
            copie.cartes_par_tirage,
            config.MAX_NOEUDS_SOLVEUR,
            config.MAX_SECONDES_SOLVEUR,
            depart,
        )
        self._copie_analyse = copie
        self._depart_analyse = depart
        self._coups_au_lancement_analyse = self.partie.nb_coups
        self.bouton_analyse.configure(state=tk.DISABLED)
        self.message("Analyse en cours… (Échap pour interrompre)")
        self.fen.after_idle(self._pas_analyse)

    def _pas_analyse(self) -> None:
        """Exécute un lot d'itérations de la recherche (~20 ms), puis se
        replanifie : c'est ce découpage qui garde l'interface réactive."""
        if self._gen_analyse is None:
            return
        limite = time.monotonic() + 0.02
        try:
            while time.monotonic() < limite:
                verdict, donnee, noeuds = next(self._gen_analyse)
                if verdict != "progres":
                    self._terminer_analyse(verdict, donnee, noeuds)
                    return
        except StopIteration:
            self._gen_analyse = None
            self.bouton_analyse.configure(state=tk.NORMAL)
            return
        self.fen.after(1, self._pas_analyse)

    def _terminer_analyse(self, verdict: str, donnee, noeuds: int) -> None:
        duree = time.monotonic() - self._depart_analyse
        copie = self._copie_analyse
        self._gen_analyse = None
        self._copie_analyse = None
        self.bouton_analyse.configure(state=tk.NORMAL)

        if verdict == "gagnable":
            resultat = solveur.Resultat(
                solveur.GAGNABLE, solveur._convertir(copie, donnee), noeuds, duree
            )
        elif verdict == "perdue":
            resultat = solveur.Resultat(solveur.PERDUE, [], noeuds, duree)
        else:
            resultat = solveur.Resultat(solveur.INDETERMINE, [], noeuds, duree)
        self._appliquer_resultat_analyse(resultat, self._coups_au_lancement_analyse)

    def _appliquer_resultat_analyse(
        self, resultat: solveur.Resultat, coups_au_lancement: int
    ) -> None:
        if self.partie is None or self.partie.nb_coups != coups_au_lancement:
            self.message("La position a changé pendant l'analyse : relancez-la.")
            return
        if resultat.est_gagnable:
            self.solution = list(resultat.coups)
            self.message(
                f"Partie gagnable : solution en {len(self.solution)} coups. "
                "Utilisez « Indice » pour la suivre."
            )
            messagebox.showinfo("Analyse", resultat.message())
            if not self.indice_actif:
                self.basculer_indice()
        elif resultat.statut == solveur.PERDUE:
            self.solution = []
            self.message("Partie perdue : aucune solution n'existe.")
            if messagebox.askyesno("Analyse", resultat.message()):
                self.nouvelle_partie(confirmer=False)
        else:
            self.solution = []
            self.message("Analyse non concluante.")
            messagebox.showinfo("Analyse", resultat.message())

    def arreter_analyse(self) -> None:
        """Interrompt l'analyse en cours (il suffit de ne plus replanifier de
        pas : le générateur est simplement abandonné, sans thread à joindre)."""
        if self._gen_analyse is not None:
            self._gen_analyse = None
            self._copie_analyse = None
            self.bouton_analyse.configure(state=tk.NORMAL)

    # ------------------------------------------------------------------
    # Paramètres
    # ------------------------------------------------------------------

    def choisir_fond(self) -> None:
        couleur = colorchooser.askcolor(self.couleur_fond, title="Couleur de fond")
        if couleur[0] is None:
            return
        rouge, vert, bleu = couleur[0]
        self.couleur_fond = couleur[1]
        luminosite = rgb_to_hls(rouge / 255, vert / 255, bleu / 255)[1]
        self.couleur_texte = "black" if luminosite >= 0.5 else "white"
        self._appliquer_couleurs()