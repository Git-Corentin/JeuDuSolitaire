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
| Glisser-déposer | maintenir le clic et relâcher sur la destination |
| Reposer les cartes tenues | clic droit, `Échap`, ou clic hors du plateau |
| Envoyer une carte automatiquement (base, sinon colonne) | double-clic |
| Piocher | clic sur la pioche, ou `Espace` |
| Recycler la pioche épuisée | clic sur l'emplacement de la pioche |
| Annuler le dernier coup | `Ctrl+Z` (ou le bouton) |
| Indice | `H` (ou le bouton « ? ») |
| Analyser la partie | `A` (ou le bouton) |
| Nouvelle partie | `N` (ou le bouton JOUER) |

Les deux modes de manipulation cohabitent : un clic simple prend les cartes et
un second clic les pose (pratique pour viser tranquillement), tandis qu'un clic
maintenu puis relâché fait un glisser-déposer classique. C'est la distance
parcourue avant le relâchement qui distingue les deux.

Le mode de tirage (1 ou 3 cartes) se choisit avec les deux boutons du menu
**avant** de lancer une partie. Le bouton engrenage ouvre les **paramètres** :

| Réglage | Effet |
| --- | --- |
| Couleur du fond | la couleur du texte s'adapte automatiquement au contraste |
| Couleurs de l'indice | surlignage de l'origine et de la destination |
| Durée maximale d'une analyse | budget en secondes (défaut : 20 s) |
| Positions explorées au maximum | budget en nombre de positions (défaut : 1 500 000) |
| Glisser-déposer | activer ou désactiver, le clic-clic restant toujours disponible |
| Indice sans retour en arrière | interdire les coups menant à une position déjà vue |
| Finition automatique | vitesse de l'animation, en ms par coup |

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
qui découvrent une carte cachée, puis la défausse, puis la pioche, et enfin
seulement les déplacements qui ne font rien progresser. La carte à déplacer est
encadrée en jaune, la destination en rouge pointillé, et le coup est décrit en
toutes lettres sous le menu.

Surtout, **l'indice ne peut plus tourner en rond** : la partie mémorise
l'empreinte de chaque position traversée (`Partie.etats_vus`), et tout coup qui
y ramènerait est écarté. Le classique « déplace ce paquet, remets-le,
redéplace-le… » est ainsi impossible par construction. Si *tous* les coups
possibles ramènent à du déjà-vu, l'aide le dit franchement au lieu de faire
tourner le joueur indéfiniment.

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
* **coupe des coups nuls** : déplacer une carte d'un parent vers un parent
  *équivalent* (même valeur, même couleur — par exemple un valet passant d'une
  dame noire à l'autre) ne change rien à la position. Sans cette règle, la
  recherche fait osciller une carte entre deux colonnes et produit des
  solutions absurdes : sur une donne d'essai, le valet de cœur était déplacé
  95 fois et le 9 de cœur 130 fois, pour 425 coups inutiles sur 549. Avec la
  règle, la même donne se résout en 163 coups sans qu'aucune carte ne soit
  déplacée deux fois, et la recherche est passée de 947 à 144 positions
  explorées ;
* **détection de position ouverte** : dès qu'il ne reste plus aucune carte
  face cachée, la victoire est certaine ; la fin de partie est alors produite
  par un algorithme glouton au lieu d'être cherchée.

L'analyse ne bloque pas l'interface, mais **pas au moyen d'un thread** : Tk et
Xlib s'accommodent mal qu'un second thread existe en parallèle du thread
principal, même s'il ne touche à aucun widget (c'est exactement le plantage
`[xcb] Unknown sequence number` / `XInitThreads` que l'on peut rencontrer sous
Linux). La recherche est donc un générateur Python, repris par petits lots
d'environ 20 ms via `fen.after()` : tout se passe dans le thread principal, et
l'interface reste réactive de la même façon. Elle peut être interrompue par
`Échap`. Budget par défaut : 1 500 000 positions ou 20 secondes, réglable dans
les paramètres.

Une analyse non concluante n'est pas perdue : le générateur reste **en pause**
avec toute sa table de transposition. Relancer l'analyse sur la même position
prolonge le budget et **reprend l'exploration exactement où elle s'était
arrêtée** — relancer trois fois explore donc trois budgets cumulés, et non
trois fois les mêmes positions. À titre indicatif, la plupart des donnes sont tranchées
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

Vingt-quatre tests couvrent la donne, les règles, la pioche et son recyclage,
l'annulation, la validité des coups conseillés et la validité des solutions
produites par le solveur (chaque solution trouvée est rejouée sur le modèle et
doit aboutir à une victoire). Trois tests verrouillent spécifiquement les
non-régressions de l'aide : aucune position répétée en suivant 150 indices
d'affilée, aucune carte baladée entre colonnes équivalentes dans une solution,
et accumulation effective des nœuds lors de la reprise d'une analyse.