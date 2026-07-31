# Solitaire (Klondike) — Python / tkinter

Jeu du solitaire complet en Python, avec interface tkinter, aide au joueur
(indice « meilleur coup ») et **solveur** capable de dire si une partie est
encore gagnable — et, le cas échéant, de fournir la suite de coups qui mène à
la victoire.

Aucune dépendance externe : uniquement la bibliothèque standard.

---

## Installation et lancement

Prérequis : **Python 3.10 ou plus**, avec le module `tkinter` (Tk 8.6).

```bash
# Debian / Ubuntu, si tkinter manque
sudo apt install python3-tk

python main.py
```

Le dossier `Images/` doit se trouver à la racine du projet, à côté de
`main.py` (il contient les 52 cartes, les dos, les bases, les repères et les
éléments du menu). Les chemins sont désormais calculés à partir de
l'emplacement du code : le jeu se lance depuis n'importe quel répertoire
courant.

### Options

| Option | Effet |
| --- | --- |
| `--tirage 1` / `--tirage 3` | nombre de cartes retournées à chaque pioche (défaut : 1) |
| `--graine 42` | rejoue exactement la même donne (utile pour tester ou pour comparer des scores) |
| `--echelle 3/4` | force l'échelle d'affichage (par défaut déduite de la taille de l'écran) |
| `--images /chemin/Images` | utilise un autre dossier d'images |

```bash
python main.py --tirage 3 --graine 2026
```

---

## Commandes

| Action | Commande |
| --- | --- |
| Prendre une carte (ou un paquet de cartes) | clic gauche dessus |
| Poser les cartes tenues | clic gauche sur la destination |
| Reposer les cartes tenues | clic droit, `Échap`, ou clic hors du plateau |
| Envoyer une carte automatiquement (base, sinon colonne) | double-clic |
| Piocher | clic sur la pioche, ou `Espace` |
| Recycler la pioche épuisée | clic sur l'emplacement de la pioche |
| Annuler le dernier coup | `Ctrl+Z` (ou le bouton) |
| Indice | `H` (ou le bouton « ? ») |
| Analyser la partie | `A` (ou le bouton) |
| Nouvelle partie | `N` (ou le bouton JOUER) |

Le mode de tirage (1 ou 3 cartes) se choisit avec les deux boutons du menu
**avant** de lancer une partie. Le bouton engrenage change la couleur du fond
(la couleur du texte s'adapte automatiquement).

---

## Règles et score

Règles classiques du Klondike : sept colonnes, quatre bases à monter de l'As au
Roi par symbole, suites descendantes de couleurs alternées dans le tableau,
seuls les Rois peuvent occuper une colonne vide. Une carte cachée est
retournée automatiquement dès qu'elle se retrouve en bas de sa colonne.

Barème (proche du barème « standard » de Windows) :

| Événement | Points |
| --- | --- |
| Défausse → colonne | +5 |
| Retournement d'une carte cachée | +5 |
| Vers une base | +10 |
| Base → colonne | −15 |
| Recyclage de la pioche | −100 (tirage 1) / −20 (tirage 3) |

Le score ne peut pas devenir négatif.

---

## L'aide au joueur

Deux outils complémentaires, tous deux dans `solitaire/solveur.py`.

### 1. Indice (instantané)

`meilleur_coup()` note tous les coups légaux et propose le meilleur selon une
heuristique simple : montées « sûres » vers les bases d'abord, puis les coups
qui découvrent une carte cachée, puis la défausse, etc. La carte à déplacer est
encadrée en jaune, la destination en rouge pointillé, et le coup est décrit en
toutes lettres sous le menu.

### 2. Analyse (recherche exhaustive)

`analyser()` explore l'arbre de jeu en profondeur d'abord et répond par l'un de
ces trois verdicts :

* **gagnable** — une solution complète a été trouvée ; elle est alors mémorisée
  et le bouton « Indice » vous guide coup par coup le long de cette solution
  (« solution : N coups restants ») ;
* **perdue** — l'arbre a été **entièrement** exploré sans trouver de victoire :
  la partie est mathématiquement perdue ;
* **indéterminé** — le budget de recherche a été épuisé avant de conclure.

Ce qui rend la recherche praticable :

* état compact (tuples d'entiers, une carte = un entier de 0 à 51) ;
* table de transposition sur une clé canonique — l'ordre des colonnes n'ayant
  aucune importance, les positions équivalentes ne sont explorées qu'une fois ;
* **coups forcés** : lorsqu'une carte peut monter « en sécurité » sur sa base
  (règle classique : les deux bases de la couleur opposée sont au moins à
  valeur − 1, l'autre base de la même couleur à valeur − 2), c'est le seul coup
  engendré ;
* **coupe des coups inutiles** : déménager une colonne entière vers une autre
  colonne vide, redescendre une carte d'une base sans qu'aucune carte
  disponible puisse s'y accrocher, etc. ;
* **détection de position ouverte** : dès qu'il ne reste plus aucune carte
  face cachée, la victoire est certaine ; la fin de partie est alors produite
  par un algorithme glouton au lieu d'être cherchée.

L'analyse tourne dans un fil d'exécution séparé (l'interface reste réactive) et
peut être interrompue par `Échap`. Budget par défaut : 1 500 000 positions ou
20 secondes (constantes `MAX_NOEUDS_SOLVEUR` et `MAX_SECONDES_SOLVEUR` dans
`solitaire/config.py`). À titre indicatif, la plupart des donnes sont tranchées
en moins d'une seconde ; quelques-unes résistent au budget complet.

Quand toutes les cartes sont retournées, le jeu propose de **terminer
automatiquement** la partie.

---

## Organisation du code

```
.
├── main.py                 point d'entrée et analyse des arguments
├── README.md
├── Images/                 les 82 images du jeu (PNG)
├── solitaire/
│   ├── __init__.py
│   ├── config.py           constantes : chemins, géométrie, couleurs, budgets
│   ├── cartes.py           la carte à jouer (objet immuable et hachable)
│   ├── partie.py           état de la partie + règles (aucune dépendance à tkinter)
│   ├── solveur.py          indice heuristique et analyse de solvabilité
│   ├── assets.py           chargement et mise à l'échelle des images
│   └── ui.py               interface tkinter
└── tests/                  tests unitaires (modèle et solveur)
```

Le principe directeur : **l'interface ne connaît aucune règle**. Un clic est
traduit en `Coup`, le modèle le valide et l'applique, puis l'écran est redessiné
à partir de l'état du modèle. Toute la comptabilité manuelle des objets du
canevas (et les désynchronisations qu'elle entraînait) a disparu.

```
ui.py  ──►  partie.py  ◄──  solveur.py
   │            ▲
   └──► assets.py, config.py
```

### Tests

```bash
python -m unittest discover -s tests -t .
```

Vingt tests couvrent la donne, les règles, la pioche et son recyclage,
l'annulation, la validité des coups conseillés et la validité des solutions
produites par le solveur (chaque solution trouvée est rejouée sur le modèle et
doit aboutir à une victoire).

---

## Ce qui a changé par rapport à la version d'origine

### Compatibilité et lancement

* **`fen.wm_state(newstate='zoomed')`** n'existe que sous Windows ; sous Linux,
  Tk répond `bad argument "zoomed": must be normal, iconic, or withdrawn`.
  La fonction `maximiser()` essaie successivement `state('zoomed')`,
  l'attribut `-zoomed` (Linux) puis une géométrie plein écran explicite.
* **`fen.iconbitmap("Images/icone.ico")`** : le fichier `.ico` était absent du
  projet et ce format n'est pas géré hors Windows → remplacé par `iconphoto()`
  avec une image PNG, dans un `try/except`.
* Les chemins `"Images/…"` étaient relatifs au **répertoire courant** : le jeu
  ne démarrait que s'il était lancé depuis son propre dossier. Ils sont
  maintenant calculés à partir de l'emplacement du module.
* `from numpy import *` + `from random import *` + `from time import *` :
  trois imports globaux qui s'écrasaient mutuellement (`random`, `shuffle`,
  `seed`, `sample` existent dans plusieurs de ces modules). numpy ne servait
  qu'à créer deux tableaux `zeros((19, 7))` : la dépendance a été supprimée,
  le projet n'utilise plus que la bibliothèque standard.
* Le jeu supposait un très grand écran (coordonnées en dur, cartes de
  140 × 196 px, plateau large de 1 870 px). L'échelle est maintenant choisie
  automatiquement selon la résolution (`--echelle` permet de la forcer) et le
  plateau est centré.

### Bugs corrigés

* **L'indice ne proposait jamais de monter une carte du tableau vers une
  base** : `if carte == derniere_carte_colonne(colonne)` comparait un *nom de
  carte* (`"Q_pique"`) à un *couple de coordonnées* `(ligne, colonne)` — la
  condition était toujours fausse. Le même test erroné existait dans `indice2`.
* **Cartes téléportées dans la dernière colonne** : en relâchant une carte
  hors du plateau après l'avoir prise dans la main ou sur une base,
  `zone_prelev[2]` et `zone_pose[2]` valaient tous deux `-1`, donc
  `test_tas_possible()` renvoyait `True` et `derniere_carte_colonne(-1)`
  désignait… la colonne 6 (indice négatif Python).
* **`indice2()` (la recherche de solution) était irrécupérable** :
  `mem_bases.copy()` ne faisait qu'une copie *superficielle* — les quatre
  listes de bases restaient partagées entre tous les états explorés ;
  `supprimer_plateau_et_visible()` et `ajouter_bases()` modifiaient leurs
  arguments au lieu de renvoyer des copies ; `test_fin()` déclarait la victoire
  dès que la pioche était vide ; la boucle s'arrêtait à `n == 100` ; un
  `try/except` nu masquait une `IndexError`. Surtout, elle était appelée par
  `print(indice2())` **à chaque nouvelle partie**, ce qui figeait l'interface au
  démarrage. Elle a été réécrite de zéro (voir « Analyse » plus haut).
* **Score « farmable »** : `score_a_jour(5, …)` n'enregistrait pas la carte dans
  `liste_score` ; il suffisait de faire l'aller-retour défausse → colonne pour
  gagner 5 points à l'infini. Le barème complet a été implémenté, avec
  pénalités.
* **Le chronomètre** tournait dans un `Thread` avec `while True` et un
  `except:` nu qui avalait toutes les erreurs ; il survivait à la fermeture de
  la fenêtre. Il utilise désormais `fen.after(1000, …)`, dans la boucle
  d'événements Tk.
* **Fuite de widgets** : `effacer_plateau()` détruisait le canevas à chaque
  partie, mais les boutons/labels étaient recréés à l'identique par-dessus.
  L'interface est maintenant construite une seule fois ; seul le dessin change.
* `global cartes_bases_bases` dans `double_clic` : variable inexistante
  (faute de frappe sans effet, mais révélatrice du problème des 40 variables
  globales).
* Les images de repère, opaques, étaient dessinées **par-dessus** les cartes :
  l'indice masquait ce qu'il désignait. Le surlignage est désormais un cadre
  jaune (origine) et un cadre rouge pointillé (destination) ; l'image de repère
  n'est utilisée que pour marquer un emplacement *vide*.
* La détection « ce clic porte-t-il sur la dernière carte du tas ? » comparait
  des noms de cartes (`plateau[coord] == plateau[derniere_carte_colonne(...)]`),
  ce qui était vrai pour deux cases vides. La position est maintenant calculée
  géométriquement à partir des listes de cartes.
* Le tableau `faces_visibles` mélangeait quatre significations dans un seul
  entier (0 = case vide, 1 = carte cachée, 2 = rouge visible, 3 = noire
  visible), et le tableau `19 × 7` imposait une hauteur de colonne arbitraire.
  Remplacés par des objets `Colonne(cachees, visibles)`.
* Retourner une carte cachée demandait un clic explicite ; c'est désormais
  automatique (règle standard), ce qui supprime toute une classe d'états
  incohérents.

### Ajouts

* Annulation illimitée des coups (`Ctrl+Z`).
* Finition automatique quand la partie est « ouverte ».
* Raccourcis clavier, messages explicatifs sous le menu.
* Donne reproductible (`--graine`), très pratique pour déboguer.
* Détection de la partie bloquée (plus aucun coup légal).
* Suite de tests unitaires.
* Message d'erreur explicite si une image est illisible par Tk (Tk 8.6 ne lit
  que PNG et GIF : un JPEG renommé en `.png` échoue avec un laconique
  `couldn't recognize data in image file`).

---

## Dépannage

| Symptôme | Cause / solution |
| --- | --- |
| `_tkinter.TclError: bad argument "zoomed"` | ancienne version du code ; corrigé par `maximiser()` |
| `ModuleNotFoundError: No module named 'tkinter'` | installer `python3-tk` (Debian/Ubuntu) |
| `Impossible de trouver le dossier des images` | placer `Images/` à côté de `main.py`, ou utiliser `--images` |
| `couldn't recognize data in image file` | l'image n'est pas un vrai PNG/GIF (JPEG renommé ?) ; reconvertir |
| Le plateau déborde de l'écran | forcer une échelle plus petite : `--echelle 2/3` ou `--echelle 1/2` |

---

## Pistes pour la suite

* Glisser-déposer véritable (maintien du bouton) en complément du clic-clic.
* Animation du déplacement des cartes et de la victoire.
* Sauvegarde de la partie en cours et tableau des meilleurs scores.
* Recherche du chemin **le plus court** (parcours en largeur ou A\*) plutôt que
  de la première solution trouvée.
* Générateur de donnes garanties gagnables, en s'appuyant sur le solveur.
