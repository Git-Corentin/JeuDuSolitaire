"""Tests du modèle de jeu (aucune dépendance à tkinter)."""

import unittest

from solitaire.cartes import Carte, jeu_complet
from solitaire.partie import Colonne, Coup, Partie


class TestDonne(unittest.TestCase):
    def test_donne_initiale(self):
        partie = Partie(graine=0)
        self.assertEqual(len(jeu_complet()), 52)
        for i, colonne in enumerate(partie.colonnes):
            self.assertEqual(len(colonne.cachees), i)
            self.assertEqual(len(colonne.visibles), 1)
        self.assertEqual(len(partie.pioche), 24)
        self.assertEqual(partie.defausse, [])

    def test_toutes_les_cartes_sont_distribuees(self):
        partie = Partie(graine=5)
        cartes = list(partie.pioche)
        for colonne in partie.colonnes:
            cartes += colonne.cachees + colonne.visibles
        self.assertEqual(sorted(cartes, key=str), sorted(jeu_complet(), key=str))

    def test_graine_reproductible(self):
        self.assertEqual(
            Partie(graine=42).instantane(), Partie(graine=42).instantane()
        )


class TestRegles(unittest.TestCase):
    def setUp(self):
        self.partie = Partie(graine=0)

    def test_pose_sur_colonne_vide(self):
        self.partie.colonnes[0] = Colonne()
        self.assertTrue(self.partie.peut_poser_sur_colonne(Carte(13, "pique"), 0))
        self.assertFalse(self.partie.peut_poser_sur_colonne(Carte(12, "pique"), 0))

    def test_alternance_des_couleurs(self):
        self.partie.colonnes[0] = Colonne(visibles=[Carte(8, "coeur")])
        self.assertTrue(self.partie.peut_poser_sur_colonne(Carte(7, "pique"), 0))
        self.assertFalse(self.partie.peut_poser_sur_colonne(Carte(7, "carreau"), 0))
        self.assertFalse(self.partie.peut_poser_sur_colonne(Carte(6, "pique"), 0))

    def test_bases_dans_l_ordre(self):
        self.assertTrue(self.partie.peut_poser_sur_base(Carte(1, "trefle")))
        self.assertFalse(self.partie.peut_poser_sur_base(Carte(2, "trefle")))
        self.partie.bases[2].append(Carte(1, "trefle"))
        self.assertTrue(self.partie.peut_poser_sur_base(Carte(2, "trefle")))

    def test_retournement_automatique(self):
        colonne = Colonne(cachees=[Carte(5, "pique")], visibles=[Carte(1, "coeur")])
        self.partie.colonnes[0] = colonne
        self.partie.appliquer(Coup("colonne", 0, "base", 0, 1, Carte(1, "coeur")))
        self.assertEqual(colonne.cachees, [])
        self.assertEqual(colonne.visibles, [Carte(5, "pique")])

    def test_coup_illegal_refuse(self):
        partie = self.partie
        carte = partie.colonnes[0].visibles[0]
        coup = Coup("colonne", 0, "colonne", 0, 1, carte)
        self.assertFalse(partie.appliquer(coup))
        self.assertEqual(partie.nb_coups, 0)


class TestPioche(unittest.TestCase):
    def test_tirage_par_trois(self):
        partie = Partie(cartes_par_tirage=3, graine=1)
        partie.appliquer(Coup("pioche"))
        self.assertEqual(len(partie.defausse), 3)
        self.assertEqual(len(partie.pioche), 21)

    def test_recyclage_conserve_l_ordre(self):
        partie = Partie(graine=1)
        ordre = list(partie.pioche)
        for _ in range(24):
            partie.appliquer(Coup("pioche"))
        self.assertEqual(partie.pioche, [])
        partie.appliquer(Coup("pioche"))  # recyclage
        self.assertEqual(partie.pioche, ordre)
        self.assertEqual(partie.defausse, [])

    def test_penalite_de_recyclage(self):
        partie = Partie(graine=1)
        partie.score = 200
        for _ in range(25):
            partie.appliquer(Coup("pioche"))
        self.assertEqual(partie.score, 100)


class TestHistorique(unittest.TestCase):
    def test_annulation(self):
        partie = Partie(graine=3)
        etat = partie.instantane()
        partie.appliquer(Coup("pioche"))
        self.assertNotEqual(partie.instantane(), etat)
        self.assertTrue(partie.annuler())
        self.assertEqual(partie.instantane(), etat)
        self.assertFalse(partie.annuler())

    def test_copie_independante(self):
        partie = Partie(graine=3)
        copie = partie.copie()
        copie.appliquer(Coup("pioche"))
        self.assertEqual(partie.defausse, [])
        self.assertEqual(len(copie.defausse), 1)


class TestFinDePartie(unittest.TestCase):
    def test_victoire(self):
        partie = Partie(graine=0)
        partie.bases = [[Carte(v, s) for v in range(1, 14)] for s in
                        ("coeur", "carreau", "trefle", "pique")]
        self.assertTrue(partie.est_gagnee)


if __name__ == "__main__":
    unittest.main()
