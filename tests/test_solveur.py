"""Tests de l'aide au joueur : indice et analyse."""

import unittest

from solitaire import solveur
from solitaire.cartes import Carte
from solitaire.partie import Colonne, Partie


def rejouer(partie: Partie, coups) -> Partie:
    """Rejoue une suite de coups sur une copie et renvoie la partie obtenue."""
    copie = partie.copie()
    for coup in coups:
        if not copie.appliquer(coup):
            raise AssertionError(f"Coup refusé par le modèle : {coup}")
    return copie


class TestIndice(unittest.TestCase):
    def test_l_as_est_conseille_en_priorite(self):
        partie = Partie(graine=0)
        partie.colonnes[0] = Colonne(visibles=[Carte(1, "pique")])
        coup = solveur.meilleur_coup(partie)
        self.assertEqual(coup.destination, "base")
        self.assertEqual(coup.carte, Carte(1, "pique"))

    def test_le_coup_conseille_est_toujours_legal(self):
        for graine in range(5):
            partie = Partie(graine=graine)
            for _ in range(40):
                coup = solveur.meilleur_coup(partie)
                self.assertIsNotNone(coup)
                self.assertTrue(partie.coup_valide(coup), coup)
                partie.appliquer(coup)


class TestAnalyse(unittest.TestCase):
    def test_solution_valide_et_gagnante(self):
        trouvees = 0
        for graine in range(6):
            partie = Partie(graine=graine)
            resultat = solveur.analyser(
                partie, max_noeuds=150_000, max_secondes=10
            )
            if resultat.est_gagnable:
                trouvees += 1
                finale = rejouer(partie, resultat.coups)
                self.assertTrue(finale.est_gagnee)
        self.assertGreaterEqual(trouvees, 3, "aucune donne résolue")

    def test_position_ouverte_toujours_gagnable(self):
        """Sans carte cachée, la victoire est certaine."""
        partie = Partie(graine=2)
        partie.pioche = []
        partie.defausse = []
        cartes = []
        for colonne in partie.colonnes:
            cartes += colonne.cachees + colonne.visibles
        cartes += partie.pioche
        # On reconstitue quatre colonnes en séquences complètes K -> A.
        partie.colonnes = [Colonne() for _ in range(7)]
        for rang, symbole in enumerate(("pique", "coeur", "trefle", "carreau")):
            partie.colonnes[rang].visibles = [
                Carte(valeur, symbole) for valeur in range(13, 0, -1)
            ]
        self.assertTrue(partie.est_ouverte)
        coups = solveur.solution_partie_ouverte(partie)
        self.assertIsNotNone(coups)
        self.assertTrue(rejouer(partie, coups).est_gagnee)

    def test_partie_perdue_detectee(self):
        """Une position sans aucun coup utile est déclarée perdue."""
        partie = Partie(graine=0)
        partie.pioche = []
        partie.defausse = []
        partie.bases = [[] for _ in range(4)]
        # Deux colonnes bloquées l'une par l'autre, aucun As accessible.
        partie.colonnes = [Colonne() for _ in range(7)]
        partie.colonnes[0] = Colonne(
            cachees=[Carte(1, "coeur")], visibles=[Carte(5, "pique")]
        )
        partie.colonnes[1] = Colonne(
            cachees=[Carte(1, "pique")], visibles=[Carte(5, "trefle")]
        )
        resultat = solveur.analyser(partie, max_noeuds=50_000, max_secondes=5)
        self.assertEqual(resultat.statut, solveur.PERDUE)

    def test_arret_demande(self):
        partie = Partie(graine=0)
        resultat = solveur.analyser(partie, doit_arreter=lambda: True)
        self.assertIn(resultat.statut, (solveur.INDETERMINE, solveur.GAGNABLE))


if __name__ == "__main__":
    unittest.main()
