"""Constantes de configuration : chemins, géométrie du plateau, couleurs.

Toutes les dimensions sont exprimées dans « l'unité de référence » : celle des
images d'origine (une carte fait 140x196 pixels). La fenêtre applique ensuite un
facteur d'échelle global (voir :mod:`solitaire.assets`) pour s'adapter à la
taille de l'écran.
"""

from pathlib import Path

# --------------------------------------------------------------------------
# Chemins
# --------------------------------------------------------------------------

RACINE_PROJET = Path(__file__).resolve().parent.parent

#: Dossiers dans lesquels les images sont recherchées, dans l'ordre.
DOSSIERS_IMAGES = (
    RACINE_PROJET / "Images",
    RACINE_PROJET / "images",
    Path.cwd() / "Images",
)

# --------------------------------------------------------------------------
# Géométrie des cartes
# --------------------------------------------------------------------------

LARGEUR_CARTE = 140
HAUTEUR_CARTE = 196

#: Distance horizontale entre deux colonnes du tableau.
ECART_COLONNES = 148
#: Décalage vertical entre deux cartes face visible d'une colonne.
ECART_VISIBLE = 38
#: Décalage vertical entre deux cartes face cachée d'une colonne.
ECART_CACHEE = 10
#: Décalage horizontal entre les cartes étalées de la défausse.
ECART_DEFAUSSE = 70

# --------------------------------------------------------------------------
# Position des différentes zones (centre des images)
# --------------------------------------------------------------------------

#: Abscisse de la première colonne / de la pioche.
X_PLATEAU = 800
#: Ordonnée de la rangée du haut (pioche, défausse, bases).
Y_RANGEE_HAUTE = 150
#: Ordonnée de la première carte des colonnes.
Y_COLONNES = 375

COORD_PIOCHE = (X_PLATEAU, Y_RANGEE_HAUTE)
COORDS_DEFAUSSE = tuple(
    (X_PLATEAU + 150 + ECART_DEFAUSSE * i, Y_RANGEE_HAUTE) for i in range(3)
)
COORDS_BASES = tuple(
    (X_PLATEAU + (3 + i) * ECART_COLONNES, Y_RANGEE_HAUTE) for i in range(4)
)

#: Nombre maximal de cartes empilables dans une colonne (6 cachées + K..A).
HAUTEUR_MAX_COLONNE = 19

#: Dimensions minimales nécessaires pour afficher le jeu entier.
LARGEUR_REFERENCE = X_PLATEAU + 6 * ECART_COLONNES + LARGEUR_CARTE + 40
HAUTEUR_REFERENCE = (
    Y_COLONNES
    + 6 * ECART_CACHEE
    + 12 * ECART_VISIBLE
    + HAUTEUR_CARTE // 2
    + 40
)

# --------------------------------------------------------------------------
# Panneau de gauche (menu)
# --------------------------------------------------------------------------

COORD_LOGO = (370, 330)
X_MENU = 150
Y_TEMPS = 60
Y_SCORE = 130
Y_BOUTON_JOUER = 560
Y_RADIOS = 690
Y_BOUTONS_OUTILS = 790
Y_BOUTON_ANALYSE = 890
Y_BOUTON_ANNULER = 940
Y_MESSAGE = 995

# --------------------------------------------------------------------------
# Apparence
# --------------------------------------------------------------------------

COULEUR_FOND_DEFAUT = "#0f7a35"
POLICE_LABEL = "Cambria 30"

#: Échelles autorisées (numérateur, dénominateur) de la plus grande à la plus
#: petite. tkinter ne sait redimensionner une PhotoImage que par des rapports
#: entiers (``zoom`` / ``subsample``), d'où ces fractions.
ECHELLES = ((1, 1), (5, 6), (3, 4), (2, 3), (1, 2), (2, 5), (1, 3))

# --------------------------------------------------------------------------
# Solveur
# --------------------------------------------------------------------------

MAX_NOEUDS_SOLVEUR = 1_500_000
MAX_SECONDES_SOLVEUR = 20.0

#: Vitesse de la finition automatique, en millisecondes par coup.
MS_PAR_COUP_FINITION = 40

#: Couleurs du surlignage de l'indice (origine et destination).
COULEUR_SURLIGNAGE_DEFAUT = "#ffd400"
COULEUR_DESTINATION_DEFAUT = "#ff5252"
