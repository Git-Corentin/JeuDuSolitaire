from tkinter import *
from numpy import *
from random import *
from tkinter.messagebox import *
from tkinter.colorchooser import *
from threading import Thread
from time import *
from colorsys import *

def zone_clic(x, y):
    if appartient_intervalle(x, coords_tas[0, 0][0] - 118 / 2, coords_tas[0, 6][0] + 118 / 2) and appartient_intervalle(y, coords_tas[0, 0][1] - 182 / 2, coords_tas[18 - 1, 0][1] + 182 / 2):  # Le clic a été fait sur un tas
        coord = convertir_pixel_coord(x, y)
        if plateau[coord] == plateau[derniere_carte_colonne(coord[1])]:  # Le clic a été fait sur une carte en bas d'un tas
            if faces_visibles[coord] == 1:  # La dernière carte est cachée
                return 1, coord[0], coord[1]
            elif faces_visibles[coord] >= 2 or faces_visibles[coord] == 0:  # La dernière carte est visible ou le tas est vide
                return (0, coord[0], coord[1])
        elif faces_visibles[coord] == 1:  # Le clic a été fait sur une carte retournée qui n'est pas la dernière
            return (0, -1, coord[1])
        elif faces_visibles[coord] >= 2:  # Le clic a été fait sur une carte visible qui n'est pas la dernière
            return (0, coord[0], coord[1])
    elif appartient_intervalle(x, coord_pioche[0] - 118 / 2, coord_pioche[0] + 118 / 2) and appartient_intervalle(y, coord_pioche[1] - 182 / 2, coord_pioche[1] + 182 / 2):  # Le clic a été fait sur la pioche
        return (2, -1, -1)
    elif appartient_intervalle(x, coords_main[0][0] - 118 / 2, coords_main[2][0] + 118 / 2) and appartient_intervalle(y, coords_main[0][1] - 182 / 2, coords_main[0][1] + 182 / 2):  # Le clic a été fait sur la main
        return (3, -1, -1)
    elif appartient_intervalle(x, coords_bases[0][0] - 118 / 2, coords_bases[0][0] + 118 / 2) and appartient_intervalle(y, coords_bases[0][1] - 182 / 2, coords_bases[0][1] + 182 / 2):  # Le clic a été fait sur la base coeur
        return (4, -1, -1)
    elif appartient_intervalle(x, coords_bases[1][0] - 118 / 2, coords_bases[1][0] + 118 / 2) and appartient_intervalle(y, coords_bases[1][1] - 182 / 2, coords_bases[1][1] + 182 / 2):  # Le clic a été fait sur la base carreau
        return (5, -1, -1)
    elif appartient_intervalle(x, coords_bases[2][0] - 118 / 2, coords_bases[2][0] + 118 / 2) and appartient_intervalle(y, coords_bases[2][1] - 182 / 2, coords_bases[2][1] + 182 / 2):  # Le clic a été fait sur la base trefle
        return (6, -1, -1)
    elif appartient_intervalle(x, coords_bases[3][0] - 118 / 2, coords_bases[3][0] + 118 / 2) and appartient_intervalle(y, coords_bases[3][1] - 182 / 2, coords_bases[3][1] + 182 / 2):  # Le clic a été fait sur la base pique
        return (7, -1, -1)
    return (-1, -1, -1)

def clic_prelev(event):
    global zone_prelev, cartes_prelev, faces_visibles, coords_tas, main, cartes_bases
    zone_prelev = zone_clic(event.x, event.y)
    test = False
    if zone_prelev[0] == 0 and zone_prelev[1] != -1 and faces_visibles[zone_prelev[1], zone_prelev[2]] != 0:  # Le clic a été fait sur un tas
        derniere = derniere_carte_colonne(zone_prelev[2])
        for i in range(zone_prelev[1], derniere[0] + 1):
            cartes_prelev.append(plateau[i, zone_prelev[2]])
        tableaux_a_jour('prelev')
        test = True
    elif zone_prelev[0] == 1:  # Le clic a été effectué sur une carte retournée
        nom = plateau[derniere_carte_colonne(zone_prelev[2])]
        can.delete(nom)
        can.create_image(coords_tas[zone_prelev[1], zone_prelev[2]], image=images_cartes[nom], tag=nom)
        faces_visibles[zone_prelev[1], zone_prelev[2]] = couleur_carte(nom)
        coord_carte = coords_tas[zone_prelev[1], zone_prelev[2]]
        k = 0
        for i in range(zone_prelev[1], 19):  # Permet de modifier les coordonnées des cartes qui seront placées en dessous
            coords_tas[i, zone_prelev[2]] = (coord_carte[0], coord_carte[1] + k)
            k += 38
        gestion_indice('prelev')
    elif zone_prelev[0] == 2:
        affichage_main()
        gestion_indice('prelev')
    elif zone_prelev[0] == 3 and len(main) != 0:
        cartes_prelev.append(main[-1])
        del main[-1]
        test = True
    elif zone_prelev[0] == 4 and len(cartes_bases[0]) != 0:
        cartes_prelev.append(cartes_bases[0][-1])
        del cartes_bases[0][-1]
        test = True
    elif zone_prelev[0] == 5 and len(cartes_bases[1]) != 0:
        cartes_prelev.append(cartes_bases[1][-1])
        del cartes_bases[1][-1]
        test = True
    elif zone_prelev[0] == 6 and len(cartes_bases[2]) != 0:
        cartes_prelev.append(cartes_bases[2][-1])
        del cartes_bases[2][-1]
        test = True
    elif zone_prelev[0] == 7 and len(cartes_bases[3]) != 0:
        cartes_prelev.append(cartes_bases[3][-1])
        del cartes_bases[3][-1]
        test = True
    if test:
        bind_pose()
        gestion_indice('prelev')

def clic_pose(event):
    global cartes_prelev, zone_pose, cartes_bases
    zone_pose = zone_clic(event.x, event.y)
    test = False
    if (zone_pose[0] == 0 or (zone_prelev[2] == zone_pose[2] and zone_prelev[2] != -1)) and test_tas_possible():  # On pose sur un tas, la deuxième condition permet de reposer sur le tas sur lequel on vient juste de prélever
        derniere = derniere_carte_colonne(zone_pose[2])
        for i in range(len(cartes_prelev)):
            can.coords(cartes_prelev[i], coords_tas[derniere[0] + 1 + i, derniere[1]])
            can.tag_raise(cartes_prelev[i])
        tableaux_a_jour('pose')
        test = True
        if zone_prelev[0] == 3:
            score_a_jour(5, cartes_prelev[0])

    elif zone_pose[0] == 3 and zone_prelev[0] == 3:  # Cas où on veut reposer la carte que l'on vient de tirer dans la main
        can.coords(cartes_prelev[0], coords_main[len(main)])
        can.tag_raise(cartes_prelev[0])
        main.append(cartes_prelev[0])
        test = True

    elif zone_pose[0] == 4 and len(cartes_prelev) == 1 and test_base_possible('coeur'):
        can.coords(cartes_prelev[0], coords_bases[0])
        can.tag_raise(cartes_prelev[0])
        cartes_bases[0].append(cartes_prelev[0])
        test = True
        score_a_jour(10, cartes_prelev[0])

    elif zone_pose[0] == 5 and len(cartes_prelev) == 1 and test_base_possible('carreau'):
        can.coords(cartes_prelev[0], coords_bases[1])
        can.tag_raise(cartes_prelev[0])
        cartes_bases[1].append(cartes_prelev[0])
        test = True
        score_a_jour(10, cartes_prelev[0])

    elif zone_pose[0] == 6 and len(cartes_prelev) == 1 and test_base_possible('trefle'):
        can.coords(cartes_prelev[0], coords_bases[2])
        can.tag_raise(cartes_prelev[0])
        cartes_bases[2].append(cartes_prelev[0])
        test = True
        score_a_jour(10, cartes_prelev[0])

    elif zone_pose[0] == 7 and len(cartes_prelev) == 1 and test_base_possible('pique'):
        can.coords(cartes_prelev[0], coords_bases[3])
        can.tag_raise(cartes_prelev[0])
        cartes_bases[3].append(cartes_prelev[0])
        test = True
        score_a_jour(10, cartes_prelev[0])
    if test:
        bind_prelev()
        cartes_prelev = []
        gestion_indice('pose')
    test_fin_jeu()

def clic_annule(event=0):
    global cartes_prelev, main, cartes_bases
    if len(cartes_prelev) != 0:
        test = False
        if zone_prelev[0] == 0:
            derniere = derniere_carte_colonne(zone_prelev[2])
            for i in range(len(cartes_prelev)):
                can.coords(cartes_prelev[i], coords_tas[derniere[0] + 1 + i, derniere[1]])
                can.tag_raise(cartes_prelev[i])
            tableaux_a_jour('annule')
            test = True
        elif zone_prelev[0] == 3:
            can.coords(cartes_prelev[0], coords_main[len(main)])
            can.tag_raise(cartes_prelev[0])
            main.append(cartes_prelev[0])
            test = True
        elif zone_prelev[0] >= 4:  # A partir des bases
            can.coords(cartes_prelev[0], coords_bases[ordre_symboles[convertir_en_liste(cartes_prelev[0])[1]]])
            can.tag_raise(cartes_prelev[0])
            cartes_bases[ordre_symboles[convertir_en_liste(cartes_prelev[0])[1]]].append(cartes_prelev[0])
            test = True
        if test:
            cartes_prelev = []
            bind_prelev()
        gestion_indice('annule')

def double_clic(event):
    global cartes_prelev, cartes_bases_bases, zone_pose
    if zone_prelev[0] == 2:
        affichage_main()
        gestion_indice('prelev')
        zone_pose = (2, -1, -1)  # Sert pour les indices
    elif len(cartes_prelev) != 0:

        if len(cartes_prelev) == 1 and test_base_possible(convertir_en_liste(cartes_prelev[0])[1]) and zone_prelev[0] < 4:  # Test dans les bases
            can.coords(cartes_prelev[0], coords_bases[ordre_symboles[convertir_en_liste(cartes_prelev[0])[1]]])
            can.tag_raise(cartes_prelev[0])
            cartes_bases[ordre_symboles[convertir_en_liste(cartes_prelev[0])[1]]].append(cartes_prelev[0])
            bind_prelev()
            score_a_jour(10, cartes_prelev[0])
            cartes_prelev = []
            zone_pose = (2, -1, -1)
            gestion_indice('double')

        else:  # Test dans les tas
            fin = False
            for i in range(7):
                zone_pose = (-1, -1, i)
                if test_tas_possible() and zone_pose[2] != zone_prelev[2]:
                    derniere = derniere_carte_colonne(zone_pose[2])
                    for j in range(len(cartes_prelev)):
                        can.coords(cartes_prelev[j], coords_tas[derniere[0] + 1 + j, derniere[1]])
                        can.tag_raise(cartes_prelev[j])
                    tableaux_a_jour('pose')
                    bind_prelev()
                    if zone_prelev[0] == 3:
                        score_a_jour(5, cartes_prelev[0])
                    zone_pose = (0, -1, i)  # Sert pour les indices, le -1 est arbitraire car non utilisé
                    gestion_indice('double')
                    cartes_prelev = []

                    fin = True
                    break
            if not fin:
                clic_annule()
    test_fin_jeu()

def bouge(event):
    if len(cartes_prelev) != 0:
        x, y = event.x, event.y
        if x < 750:
            x = 750
        for i in range(len(cartes_prelev)):
            if len(cartes_prelev) == 1:
                can.coords(cartes_prelev[i], x, y + 38 * i)
            else:
                can.coords(cartes_prelev[i], x, y + 38 * i + 65)
            can.tag_raise(cartes_prelev[i])

def test_tas_possible():
    if zone_prelev[2] == zone_pose[2]:
        return True
    # elif faces_visibles[0, zone_pose[2]] == 0:
    elif plateau[0, zone_pose[2]] == 0:
        if 'K' in cartes_prelev[0]:
            return True

    elif couleur_carte(cartes_prelev[0]) != couleur_carte(plateau[derniere_carte_colonne(zone_pose[2])]):
        if convertir_valeur_nombre(convertir_en_liste(cartes_prelev[0])[0]) + 1 == convertir_valeur_nombre(convertir_en_liste(plateau[derniere_carte_colonne(zone_pose[2])])[0]):
            return True
    return False

def test_base_possible(symbole):
    if convertir_en_liste(cartes_prelev[0])[1] == symbole:
        rang = ordre_symboles[symbole]
        if len(cartes_bases[rang]) == 0 and convertir_en_liste(cartes_prelev[0])[0] == 'A':
            return True
        elif len(cartes_bases[rang]) != 0 and convertir_valeur_nombre(convertir_en_liste(cartes_prelev[0])[0]) == convertir_valeur_nombre(convertir_en_liste(cartes_bases[rang][-1])[0]) + 1:
            return True
    return False

def test_fin_jeu():
    global etat_chrono
    if len(cartes_bases[0]) == 13 and len(cartes_bases[1]) == 13 and len(cartes_bases[2]) == 13 and len(cartes_bases[3]) == 13:
        print('\n\nVOUS AVEZ GAGNE !!\n\n')
        can.unbind("<Button-1>")
        can.unbind("<Double-Button-1>")
        etat_chrono = False
        messbox = askquestion("Victoire !", "VOUS AVEZ GAGNÉ !!!\n\nVoulez-vous rejouer ?")
        if messbox == 'yes':
            debut_partie()
        else:
            fen.destroy()

def score_a_jour(valeur, nom):
    global score
    if not nom in liste_score:
        score += valeur
        label_score.configure(text="Score : " + str(score))
        if valeur == 10:
            liste_score.append(nom)

def tableaux_a_jour(appel):
    global plateau, faces_visibles, derniere
    if appel == 'pose':
        derniere = derniere_carte_colonne(zone_pose[2])
    if appel == 'annule':
        derniere = derniere_carte_colonne(zone_prelev[2])
    for i in range(len(cartes_prelev)):
        if appel == 'prelev':
            plateau[zone_prelev[1] + i, zone_prelev[2]] = 0
            faces_visibles[zone_prelev[1] + i, zone_prelev[2]] = 0
        else:
            plateau[derniere[0] + 1 + i, derniere[1]] = cartes_prelev[i]
            faces_visibles[derniere[0] + 1 + i, derniere[1]] = couleur_carte(cartes_prelev[i])

def affichage_main():
    global main, fosse, paquet
    if len(main) != 0:
        for i in main:
            can.delete(i)
            fosse.append(i)
        main = []
    if len(paquet) == 0:
        paquet = fosse.copy()
        fosse = []
        can.delete('retourne')
        can.create_image(coord_pioche, image=image_dos, tag='pioche')
    else:
        for i in range(nombre_cartes):
            if len(paquet) != 0:
                main.append(paquet[0])
                del paquet[0]
        for i in range(len(main)):
            can.create_image(coords_main[i], image=images_cartes[main[i]], tag=main[i])
        if len(paquet) == 0:
            can.delete('pioche')
            can.create_image(coord_pioche, image=image_retourne, tag='retourne')

def bind_prelev():
    can.bind("<Button-1>", clic_prelev)
    can.unbind("<Button-3>")

def bind_pose():
    can.bind("<Button-1>", clic_pose)
    can.bind("<Button-3>", clic_annule)

def appartient_intervalle(x, a, b):
    '''Renvoie True si x est compris dans l'intervalle [a,b]'''
    if x >= a and x <= b:
        return True
    return False

def convertir_pixel_coord(x, y):
    for ligne in range(19):
        for colonne in range(7):
            if faces_visibles[ligne, colonne] == 1:  # Carte retournée
                if plateau[ligne, colonne] == plateau[derniere_carte_colonne(colonne)]:  # Carte en bas du tas
                    if appartient_intervalle(x, coords_tas[ligne, colonne][0] - 118 / 2, coords_tas[ligne, colonne][0] + 118 / 2) and appartient_intervalle(y, coords_tas[ligne, colonne][1] - 182 / 2, coords_tas[ligne, colonne][1] + 182 / 2):
                        return (ligne, colonne)
                else:  # Carte pas en bas du tas
                    if appartient_intervalle(x, coords_tas[ligne, colonne][0] - 118 / 2, coords_tas[ligne, colonne][0] + 118 / 2) and appartient_intervalle(y, coords_tas[ligne, colonne][1] - 182 / 2, coords_tas[ligne, colonne][1] - 182 / 2 + 10):
                        return (ligne, colonne)
            elif faces_visibles[ligne, colonne] >= 2:  # Carte visible
                if plateau[ligne, colonne] == plateau[derniere_carte_colonne(colonne)]:  # Carte en bas du tas
                    if appartient_intervalle(x, coords_tas[ligne, colonne][0] - 118 / 2, coords_tas[ligne, colonne][0] + 118 / 2) and appartient_intervalle(y, coords_tas[ligne, colonne][1] - 182 / 2, coords_tas[ligne, colonne][1] + 182 / 2):
                        return (ligne, colonne)
                else:  # Carte pas en bas du tas
                    if appartient_intervalle(x, coords_tas[ligne, colonne][0] - 118 / 2, coords_tas[ligne, colonne][0] + 118 / 2) and appartient_intervalle(y, coords_tas[ligne, colonne][1] - 182 / 2, coords_tas[ligne, colonne][1] - 182 / 2 + 38):
                        return (ligne, colonne)
            elif faces_visibles[ligne, colonne] == 0:  # Dans le cas où le tas est vide
                if appartient_intervalle(x, coords_tas[ligne, colonne][0] - 118 / 2, coords_tas[ligne, colonne][0] + 118 / 2) and appartient_intervalle(y, coords_tas[ligne, colonne][1] - 182 / 2, coords_tas[ligne, colonne][1] + 182 / 2):
                    return (ligne, colonne)
    return (-1, -1)

def derniere_carte_colonne(colonne):
    for ligne in range(-1, 18):
        if faces_visibles[ligne + 1, colonne] == 0:
            return (ligne, colonne)
    return (18, colonne)

def debut_chrono():
    global etat_chrono, chrono
    while True:
        try:
            if etat_chrono:
                sleep(1)
                chrono[2] += 1
                if chrono[2] == 60:
                    chrono[2] = 0
                    chrono[1] += 1
                if chrono[1] == 60:
                    chrono[1] = 0
                    chrono[0] += 1
                label_temps.configure(text="Temps : " + str(chrono[0]) + ":" + str(chrono[1]) + ":" + str(chrono[2]))
            if etat_chrono == 'quit':
                break
        except:
            if etat_chrono == 'quit':
                break
            etat_chrono = False

def intercepte():
    global etat_chrono
    etat_chrono = 'quit'
    fen.destroy()

def import_cartes():
    '''Importe toutes les images de cartes'''
    D = {}
    for i in symboles:
        for j in valeurs:
            D[j + '_' + i] = PhotoImage(file='Images/' + j + '_' + i + '.png')
    return D

def import_bases():
    '''Importe les images des quatres bases'''
    L = []
    for i in symboles:
        L.append(PhotoImage(file='Images/base_' + i + '.png'))
    return L

def import_reperes():
    L = []
    for i in range(1, 14):
        L.append(PhotoImage(file='Images/repere' + str(i) + '.png'))
    return L

def couleur_carte(nom):
    """Renvoie 2 si la carte en argument est rouge et 3 si elle est noire"""
    if 'coeur' in nom or 'carreau' in nom:
        return 2  # Carte rouge
    return 3  # Carte noire

def convertir_en_liste(nom):
    return nom.split("_")

def convertir_valeur_nombre(valeur):
    if valeur == 'K':
        return 13
    elif valeur == 'Q':
        return 12
    elif valeur == 'J':
        return 11
    elif valeur == 'A':
        return 1
    return int(valeur)

def melange_cartes():
    """Créée une liste contenant toutes les cartes du jeu mélangées. Puis place ces cartes sur le plateau initial ainsi que leur état (deux tableaux)"""
    L = []
    T1 = zeros((19, 7), dtype=object)
    T2 = zeros((19, 7), dtype=int)
    for i in symboles:
        for j in valeurs:
            L.append(j + '_' + i)
    shuffle(L)
    k = 0
    for colonne in range(7):
        for ligne in range(19):
            if ligne <= k:
                T1[ligne, colonne] = L[0]  # On remplit le plateau des sept tas de cartes

                if ligne == k:
                    T2[ligne, colonne] = couleur_carte(L[0])  # Etat de carte révélée ainsi qu'une indication de sa couleur
                else:
                    T2[ligne, colonne] = 1  # Etat de carte retournée
                del L[0]
        k += 1
    return T1, L, T2

def coordonnees():
    """Renvoie un tableau contenant les coordonnée de tous les tas de cartes"""
    T = zeros((19, 7), dtype=object)
    k = 0
    x, y = 800, 375
    for colonne in range(7):
        for ligne in range(19):
            T[ligne, colonne] = (x, y)
            if ligne >= k:
                y += 38
            else:
                y += 10
        x += 148
        y = 375
        k += 1
    return T

def parametre():
    global couleur_fond, couleur_label
    couleur = askcolor(couleur_fond, title='Couleur de fond')
    if couleur[0] != None:
        couleur_fond = couleur[1]
        if rgb_to_hls(couleur[0][0] / 255, couleur[0][1] / 255, couleur[0][2] / 255)[1] * 240 >= 120:  # Si le fond est trop clair, il faut mettre les labels en noir
            couleur_label = 'black'
            label_temps.configure(fg=couleur_label)
            label_score.configure(fg=couleur_label)
        else:
            couleur_label = 'white'
            label_temps.configure(fg=couleur_label)
            label_score.configure(fg=couleur_label)
        can.configure(bg=couleur_fond, highlightbackground=couleur_fond)
        label_temps.configure(bg=couleur_fond)
        label_score.configure(bg=couleur_fond)
        bouton_jouer.configure(bg=couleur_fond, activebackground=couleur_fond)
        radiobouton_une_carte.configure(bg=couleur_fond, activebackground=couleur_fond, selectcolor=couleur_fond)
        radiobouton_trois_cartes.configure(bg=couleur_fond, activebackground=couleur_fond, selectcolor=couleur_fond)
        bouton_parametre.configure(bg=couleur_fond, activebackground=couleur_fond)
        bouton_indice.configure(bg=couleur_fond, activebackground=couleur_fond)

def appel_indice():
    global carte_indice, liste_indice

    if bouton_indice.cget("image") == str(image_indice_deselect) and etat_chrono:
        clic_annule()  # Dans le cas où on clique sur le bouton avec des cartes prélevées
        bouton_indice.configure(image=image_indice_select)
        liste_indice = indice()

        if not liste_indice:  # Aucun déplacement utile n'a été détecté
            bouton_indice.configure(image=image_indice_deselect)
            messbox = askquestion("Indice", "Aucune chance de victoire n'a été trouvée !\n\nVoulez-vous commencer une nouvelle partie ?")
            if messbox == 'yes':
                debut_partie()
        else:
            carte_indice = liste_indice.pop(0)
            afficher_indice()
    else:
        bouton_indice.configure(image=image_indice_deselect)
        can.delete('repere')
        carte_indice = []

def indice():
    # Test dans les tas pour la carte initiale

    for ligne in range(19):
        for colonne in range(7):

            if plateau[ligne, colonne] != 0 and faces_visibles[ligne, colonne] >= 2:

                carte = plateau[ligne, colonne]
                if carte == derniere_carte_colonne(colonne):
                    test_base = test_indice_bases(carte)
                    if test_base != None:
                        return [[(0, test_base + 4), (ligne, colonne), (-1, -1)]]

                test_tas = test_indice_tas(carte, colonne, ligne)
                if test_tas != None:
                    return [[(0, 0), (ligne, colonne), (test_tas[0] + 1, test_tas[1])]]
            elif ligne == derniere_carte_colonne(colonne)[0]:
                return [[(8, 8), (ligne, colonne), (-1, -1)]]

    # Test dans la pioche pour la carte initiale

    paquet_indice = main + paquet + fosse

    for i in paquet_indice:
        test_base = test_indice_bases(i)
        if test_base != None:
            return [[(2, test_base + 4, i), (-1, -1), (test_base + 4, test_base + 4)]]
        test_tas = test_indice_tas(i, -1, -1)
        if test_tas != None:
            return [[(2, 0, i), (-1, -1), (test_tas[0] + 1, test_tas[1])]]

    # Test dans les bases pour la carte initiale
    for i in range(4):
        if len(cartes_bases[i]) != 0:
            test_tas = test_indice_tas(cartes_bases[i][-1], -1, -1)
            if test_tas != None:
                return [[(i + 4, 0), (-1, -1), (test_tas[0] + 1, test_tas[1])]]
    return False

def indice2():
    def test_indice2_bases(carte, test_bases):
        base = ordre_symboles[convertir_en_liste(carte)[1]]  # Test dans les base pour la carte finale
        if len(test_bases[base]) == 0 and convertir_en_liste(carte)[0] == 'A':
            return base
        elif len(test_bases[base]) != 0 and convertir_valeur_nombre(convertir_en_liste(carte)[0]) == convertir_valeur_nombre(convertir_en_liste(test_bases[base][-1])[0]) + 1:
            return base

    def test_indice2_tas(carte, colonne, ligne, test_plateau, test_visible):
        for tas in range(7):  # Test dans les tas pour la carte finale
            if tas != colonne:  # Uniquement dans le cas où l'indice initial est dans les tas (colonne == -1 dans les autres cas donc condition respectée)
                derniere = derniere_carte_colonne(tas)
                if derniere[0] == -1:  # Tas vide
                    if 'K' in carte and ligne != 0:  # Il ne sert à rien de changer un roi de colonne s'il est déjà en haut d'un tas; #Uniquement dans le cas où l'indice initial est dans les tas (ligne == -1 dans les autres cas donc condition respectée)
                        return derniere
                elif test_visible[derniere] >= 2:  # Tas non vide
                    if couleur_carte(carte) != couleur_carte(test_plateau[derniere]):
                        if convertir_valeur_nombre(convertir_en_liste(carte)[0]) + 1 == convertir_valeur_nombre(convertir_en_liste(test_plateau[derniere])[0]):
                            return derniere
    def supprimer_plateau_et_visible(test_plateau, test_visible, coord):
        test_plateau[coord] = 0
        test_visible[coord] = 0
        if coord[0] > 0:
            test_visible[coord[0]-1, coord[1]] = couleur_carte(test_plateau[coord[0]-1, coord[1]]) #On retourne la carte lorsqu'elle est cachée
        return test_plateau, test_visible
    def ajouter_plateau_et_visible(test_plateau, test_visible, coord, carte):
        test_plateau[coord] = carte
        test_visible[coord] = couleur_carte(carte)
        return test_plateau, test_visible
    def ajouter_bases(test_bases, carte):
        test_bases[ordre_symboles[convertir_en_liste(carte)[1]]].append(carte)
        return test_bases
    def supprimer_bases(test_bases, carte):
        del test_bases[ordre_symboles[convertir_en_liste(carte)[1]]][-1]
        return test_bases
    def supprimer_paquet(test_paquet, carte):

        del test_paquet[test_paquet.index(carte)]
        return test_paquet


    def test_fin(test_paquet, test_visibles):
        if len(test_paquet) == 0 and not 1 in test_visibles:
            return True


    mem_plateau = plateau.copy()
    mem_visible = faces_visibles.copy()
    mem_bases = cartes_bases.copy()
    mem_paquet = paquet.copy()

    L = []
    rang = -1

    n = 0
    while True:
        if len(L) != 0:
            try:
                mem_plateau = L[rang][0][0].copy()
                mem_visible = L[rang][0][1].copy()

                mem_paquet = L[rang][0][2].copy()
                mem_bases = L[rang][0][3].copy()
            except:
                print(len(L))
                print(rang)

        L2 = []

        # Test dans les tas pour la carte initiale
        for ligne in range(19):
            for colonne in range(7):
                if mem_plateau[ligne, colonne] != 0 and mem_visible[ligne, colonne] >= 2:
                    carte = mem_plateau[ligne, colonne]
                    # Test dans les bases pour la carte finale
                    if carte == derniere_carte_colonne(colonne): # Seules les cartes en-bas des tas peuvent être placées dans les bases
                        test_base = test_indice2_bases(carte,mem_bases)
                        if test_base != None:
                            a = [(0, test_base + 4), (ligne, colonne), (-1, -1)]
                            b = supprimer_plateau_et_visible(mem_plateau, mem_visible, (ligne, colonne))
                            mem_plateau2, mem_visible2 = b[0].copy(), b[1].copy()
                            mem_bases2 = ajouter_bases(mem_bases, carte).copy()
                            L2.append([mem_plateau2, mem_visible2, mem_paquet, mem_bases2, a])
                            if test_fin(mem_paquet, mem_visible2):
                                return 'VICTOIRE'
                    # Test dans les tas pour la carte finale
                    test_tas = test_indice2_tas(carte, colonne, ligne, mem_plateau, mem_visible)
                    if test_tas != None:
                        a = [(0, 0), (ligne, colonne), (test_tas[0] + 1, test_tas[1])]
                        b = supprimer_plateau_et_visible(mem_plateau, mem_visible, (ligne, colonne))
                        mem_plateau2, mem_visible2 = b[0].copy(), b[1].copy()
                        c = ajouter_plateau_et_visible(mem_plateau2, mem_visible2, (test_tas[0] + 1, test_tas[1]), carte)
                        mem_plateau2, mem_visible2 = c[0].copy(), c[1].copy()
                        L2.append([mem_plateau2, mem_visible2, mem_paquet, mem_bases, a])
                        if test_fin(mem_paquet, mem_visible2):
                            return 'VICTOIRE'


        # Test dans la pioche pour la carte initiale
        for i in mem_paquet:
            # Test dans les bases pour la carte finale
            test_base = test_indice2_bases(i, mem_bases)
            if test_base != None:
                a = [(2, test_base + 4, i), (-1, -1), (test_base + 4, test_base + 4)]
                mem_paquet2 = supprimer_paquet(mem_paquet, i).copy()
                mem_bases2 = ajouter_bases(mem_bases, i).copy()
                L2.append([mem_plateau, mem_visible, mem_paquet2, mem_bases2, a])
                if test_fin(mem_paquet2, mem_visible):
                    return 'VICTOIRE'
            # Test dans les tas pour la carte finale
            test_tas = test_indice2_tas(i, -1, -1, mem_plateau, mem_visible)
            if test_tas != None:
                a = [(2, 0, i), (-1, -1), (test_tas[0] + 1, test_tas[1])]
                mem_paquet2 = supprimer_paquet(mem_paquet, i).copy()
                b = ajouter_plateau_et_visible(mem_plateau, mem_visible, (test_tas[0] + 1, test_tas[1]), i)
                mem_plateau2, mem_visible2 = b[0].copy(), b[1].copy()
                L2.append([mem_plateau2, mem_visible2, mem_paquet2, mem_bases, a])
                if test_fin(mem_paquet2, mem_visible2):
                    return 'VICTOIRE'

        # Test dans les bases pour la carte initiale
        for i in range(4):
            if len(mem_bases[i]) != 0:
                # Test dans les tas pour la carte finale
                test_tas = test_indice2_tas(mem_bases[i][-1], -1, -1, mem_plateau, mem_visible)
                if test_tas != None:
                    a = [(i + 4, 0), (-1, -1), (test_tas[0] + 1, test_tas[1])]
                    mem_bases2 = supprimer_bases(mem_bases, mem_bases[i][-1]).copy()
                    b = ajouter_plateau_et_visible(mem_plateau, mem_visible, (test_tas[0] + 1, test_tas[1]), mem_bases[i][-1])
                    mem_plateau2, mem_visible2 = b[0].copy(), b[1].copy()
                    L2.append([mem_plateau2, mem_visible2, mem_paquet, mem_bases2, a])
                    if test_fin(mem_paquet, mem_visible2):
                        return 'VICTOIRE'



        if len(L2) != 0:
            L.append(L2)
            rang+=1
        else:
            del L[rang][0]
            if len(L[rang]) == 0:
                del L[rang]
            if len(L) == 0:
                return 'vide'
        n += 1
        if n == 100:
            print('fin')
            break

    return 1
def test_indice_bases(carte):
    base = ordre_symboles[convertir_en_liste(carte)[1]]  # Test dans les base pour la carte finale
    if len(cartes_bases[base]) == 0 and convertir_en_liste(carte)[0] == 'A':
        return base
    elif len(cartes_bases[base]) != 0 and convertir_valeur_nombre(convertir_en_liste(carte)[0]) == convertir_valeur_nombre(convertir_en_liste(cartes_bases[base][-1])[0]) + 1:
        return base

def test_indice_tas(carte, colonne, ligne):
    for tas in range(7):  # Test dans les tas pour la carte finale
        if tas != colonne:
            derniere = derniere_carte_colonne(tas)
            if derniere[0] == -1:  # Tas vide
                if 'K' in carte and ligne != 0:  # Il ne sert à rien de changer un roi de colonne s'il est déjà en haut d'un tas
                    return derniere
            elif faces_visibles[derniere] >= 2:  # Tas non vide
                if couleur_carte(carte) != couleur_carte(plateau[derniere]):
                    if convertir_valeur_nombre(convertir_en_liste(carte)[0]) + 1 == convertir_valeur_nombre(convertir_en_liste(plateau[derniere])[0]):
                        return derniere

def gestion_indice(appel):
    global carte_indice
    if carte_indice != [] and bouton_indice.cget("image") == str(image_indice_select):
        fin_indice = False
        if appel == 'prelev':
            can.delete('repere')
            if (zone_prelev[0] == 0 or zone_prelev[0] == 1) and zone_prelev[1] == carte_indice[1][0] and zone_prelev[2] == carte_indice[1][1]:  # La carte a été prélevée du tas et il s'agit de la carte d'indice

                if carte_indice[0][1] == 0:  # Carte indice finale dans le tas
                    can.create_image(coords_tas[carte_indice[2]], image=images_repere[0], tag='repere')  # On affiche alors l'emplacement sur lequel il faut placer la carte indice
                elif carte_indice[0][0] == 8:  # Carte indice correspond à une carte cachée qu'il faut retourner
                    fin_indice = True
                elif carte_indice[0][1] >= 4:  # Carte indice finale dans les bases
                    can.create_image(coords_bases[carte_indice[0][1] - 4], image=images_repere[0], tag='repere')

            elif (zone_prelev[0] == 2 or zone_prelev[0] == 3) and carte_indice[0][0] == 2:  # Carte initiale dans la pioche ou la main
                afficher_indice()
                if zone_prelev[0] == 3 and carte_indice[0][2] == cartes_prelev[0]:  # On récupère la carte indice initiale dans la main
                    # if carte_indice[0][1] == 0:  # Carte indice finale dans le tas
                    # can.create_image(coords_tas[carte_indice[2]], image=images_repere[0], tag='repere')  # On affiche alors l'emplacement sur lequel il faut placer la carte indice

                    if carte_indice[0][1] == 0:  # Carte indice finale dans les tas
                        can.delete('repere')
                        can.create_image(coords_tas[carte_indice[2]], image=images_repere[0], tag='repere')

                    elif carte_indice[0][1] >= 4:  # Carte indice finale dans les bases
                        can.delete('repere')
                        can.create_image(coords_bases[carte_indice[2][0] - 4], image=images_repere[0], tag='repere')
            elif zone_prelev[0] >= 4:  # Carte indice initiale dans les bases
                if carte_indice[0][1] == 0:  # Carte indice finale dans le tas
                    can.create_image(coords_tas[carte_indice[2]], image=images_repere[0], tag='repere')

            else:
                fin_indice = True
        elif appel == 'pose' or appel == 'double':
            if zone_pose[0] == carte_indice[0][1]:
                bon_placement = False
                if zone_pose[2] == carte_indice[2][1]:  # Si on pose bien sur le tas correspondant à la carte indice
                    bon_placement = True
                elif zone_pose[0] >= 4:  # Si on pose sur une base
                    bon_placement = True
                if bon_placement:
                    can.delete('repere')
                    if len(liste_indice) != 0:  # Il reste encore des cartes indices à montrer
                        carte_indice = liste_indice.pop(0)
                        afficher_indice()
                    else:  # Il n'y a plus de carte indice à montrer
                        fin_indice = True
            else:
                fin_indice = True

            '''
            if zone_pose[0] == 0 or zone_pose[0] == 1 or (appel == 'double' and (zone_prelev[1], zone_prelev[2]) == carte_indice[1]):  # La carte est posée sur un tas; si elle est issue d'un double clic, on vérifie que celui-ci a été fait sur les coordonnées initiales de la carte indice

                if zone_pose[2] == carte_indice[2][1]:  #Si on pose bien sur le tas correspondant à la carte indice
                    can.delete('repere')
                    if len(liste_indice) != 0:  # Il reste encore des cartes indices à montrer
                        carte_indice = liste_indice.pop(0)
                        afficher_indice()
                    else:  # Il n'y a plus de carte indice à montrer
                        fin_indice = True
                else:
                    fin_indice = True
            '''
        elif appel == 'annule':
            afficher_indice()
        if fin_indice:
            can.delete('repere')
            carte_indice = []
            bouton_indice.configure(image=image_indice_deselect)

def afficher_indice():
    can.delete('repere')
    if carte_indice[0][0] == 0:  # Carte indice initiale dans le tas
        dif = derniere_carte_colonne(carte_indice[1][1])[0] - carte_indice[1][0]
        can.create_image((coords_tas[carte_indice[1]][0], coords_tas[carte_indice[1]][1] + 19 * dif), image=images_repere[dif], tag='repere')
    elif carte_indice[0][0] == 2:  # Carte indice initiale dans le paquet ou la main
        if carte_indice[0][2] in main:
            can.create_image(coords_main[0], image=images_repere[0], tag='repere')
        else:
            can.create_image(coord_pioche, image=images_repere[0], tag='repere')
    elif carte_indice[0][0] == 8:
        can.create_image(coords_tas[carte_indice[1]], image=images_repere[0], tag='repere')
    elif carte_indice[0][0] >= 4:  # Carte indice initiale dans les bases
        can.create_image(coords_bases[carte_indice[0][0] - 4], image=images_repere[0], tag='repere')

def affichage_tas():
    # Affichage tas
    for ligne in range(7):
        for colonne in range(7):
            if faces_visibles[ligne, colonne] == 1:
                can.create_image(coords_tas[ligne, colonne], image=image_dos, tag=plateau[ligne, colonne])
            elif faces_visibles[ligne, colonne] >= 2:
                can.create_image(coords_tas[ligne, colonne], image=images_cartes[plateau[ligne, colonne]], tag=plateau[ligne, colonne])

def affichage_plateau():
    """Affiche la pioche, les bases, ainsi que toutes les cartes initiales dans les tas"""
    # Affichage pioche
    can.create_image(coord_pioche, image=image_dos, tag='pioche')
    # Affichage bases
    for i in range(4):
        can.create_image(coords_bases[i], image=images_bases[i])
    # Affichage base des tas
    for colonne in range(7):
        can.create_image(coords_tas[0, colonne], image=image_vide)

def effacer_plateau():
    can.destroy()

def debut_jeu():
    global can, coords_tas, plateau, paquet, faces_visibles, cartes_prelev, cartes_bases, main, fosse, score, liste_score, label_score, label_temps, bouton_jouer, bouton_parametre, radiobouton_une_carte, radiobouton_trois_cartes, bouton_indice, carte_indice
    can = Canvas(fen, bg=couleur_fond, width=fen.winfo_screenwidth(), height=fen.winfo_screenheight(), highlightbackground=couleur_fond)
    can.pack()
    coords_tas = coordonnees()
    plateau, paquet, faces_visibles = melange_cartes()
    cartes_prelev = []
    cartes_bases = [[], [], [], []]
    main, fosse = [], []
    liste_score = []
    carte_indice = []
    affichage_plateau()
    can.create_image(370, 350, image=image_solitaire)
    bouton_jouer = Button(can, image=image_jouer, bg=couleur_fond, activebackground=couleur_fond, borderwidth=0, command=debut_partie)
    bouton_jouer.place(x=210, y=600)
    radiobouton_une_carte = Radiobutton(can, image=image_une_carte_deselect, selectimage=image_une_carte, variable=var_nb_cartes, value=1, indicatoron=0, activebackground=couleur_fond, selectcolor=couleur_fond, bg=couleur_fond, borderwidth=0)
    radiobouton_une_carte.place(x=180, y=720)
    radiobouton_trois_cartes = Radiobutton(can, image=image_trois_cartes_deselect, selectimage=image_trois_cartes, variable=var_nb_cartes, value=3, indicatoron=0, activebackground=couleur_fond, selectcolor=couleur_fond, bg=couleur_fond, borderwidth=0)
    radiobouton_trois_cartes.place(x=370, y=720)
    score = 0
    label_score = Label(can, text='Score : ' + str(score), font='Cambria 35', bg=couleur_fond, fg=couleur_label)
    label_score.place(x=200, y=130)
    label_temps = Label(can, text='Temps : 0:0:0', font='Cambria 35', bg=couleur_fond, fg=couleur_label)
    label_temps.place(x=200, y=60)
    bouton_parametre = Button(can, image=image_parametre, bg=couleur_fond, activebackground=couleur_fond, borderwidth=0, command=parametre)
    bouton_parametre.place(x=210, y=810)
    bouton_indice = Button(can, image=image_indice_deselect, bg=couleur_fond, activebackground=couleur_fond, borderwidth=0, command=appel_indice)
    bouton_indice.place(x=400, y=810)

def debut_partie():
    global nombre_cartes, etat_chrono, threading, chrono
    effacer_plateau()
    debut_jeu()
    can.bind("<Motion>", bouge)
    can.bind("<Double-Button-1>", double_clic)
    bind_prelev()
    nombre_cartes = var_nb_cartes.get()
    affichage_tas()
    etat_chrono = True
    chrono = [0, 0, 0, 0]
    print(indice2())


fen = Tk()
fen.title('Solitaire')
fen.wm_state(newstate='zoomed')
fen.protocol("WM_DELETE_WINDOW", intercepte)
fen.iconbitmap("Images/icone.ico")
symboles = ['coeur', 'carreau', 'trefle', 'pique']
valeurs = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
ordre_symboles = {'coeur': 0, 'carreau': 1, 'trefle': 2, 'pique': 3}
couleur_fond = 'green'
couleur_label = 'white'
# Importation des images
images_cartes = import_cartes()
image_dos = PhotoImage(file='Images/dos2.png')
images_bases = import_bases()
image_retourne = PhotoImage(file='Images/retourne.png')
image_vide = PhotoImage(file='Images/vide.png')
image_jouer = PhotoImage(file='Images/jouer.png')
image_solitaire = PhotoImage(file='Images/solitaire.png')
image_parametre = PhotoImage(file='Images/parametre.png')
image_indice_select = PhotoImage(file='Images/indice_select.png')
image_indice_deselect = PhotoImage(file='Images/indice_deselect.png')
images_repere = import_reperes()
image_une_carte = PhotoImage(file='Images/une_carte.png')
image_trois_cartes = PhotoImage(file='Images/trois_cartes.png')
image_une_carte_deselect = PhotoImage(file='Images/une_carte_deselect.png')
image_trois_cartes_deselect = PhotoImage(file='Images/trois_cartes_deselect.png')

var_nb_cartes = IntVar()
var_nb_cartes.set(1)

etat_chrono = False
threading = Thread(target=debut_chrono)
threading.start()
coord_pioche = (800, 150)
coords_main = [(800 + 150, 150), (800 + 220, 150), (800 + 290, 150)]
coords_bases = [(800 + 3 * 148, 150), (800 + 4 * 148, 150), (800 + 5 * 148, 150), (800 + 6 * 148, 150)]
debut_jeu()

fen.mainloop()
