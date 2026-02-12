from random import choice
from copy import deepcopy
from game import coups_possibles, jouer_coup, compter_jetons

# Profondeur maximale de l'arbre de jeu à explorer
profondeur_max = 3

# Cache global pour mémoriser les états déjà calculés et éviter les recalculs
cache_arbre = {}

# Statistiques pour le debug (nombre de nœuds élaguées)
stats_elagage = {"noeuds_elagues": 0, "noeuds_explores": 0}


def plateau_to_key(plateau):
    """
    Convertit le plateau en clé hashable pour le cache.
    
    Permet de sauvegarder les états du plateau pour éviter les recalculs.
    Transforme la liste 2D de Cell en tuple imbriqué (joueur, jeton).
    
    Args:
        plateau: La grille de jeu (List[List[Cell]])
    
    Returns:
        Un tuple imbriqué représentant l'état du plateau
    """
    return tuple(
        tuple((cell.joueur, cell.jeton) for cell in row)
        for row in plateau
    )


def evaluer_plateau(plateau, joueur_id, adversaire_id):
    """
    Évalue la qualité du plateau pour le joueur actuel avec analyse tactique avancée.
    
    Prend en compte:
    1. La différence de jetons (score brut)
    2. Les cellules prêtes à exploser (3 jetons) - très important!
    3. Les chaînes d'explosion potentielles
    4. Le contrôle du plateau
    5. Les menaces imminentes de l'adversaire
    
    Args:
        plateau: La grille de jeu (List[List[Cell]])
        joueur_id: ID du joueur (1 ou 2)
        adversaire_id: ID de l'adversaire
    
    Returns:
        Score évalué (int)
    """
    from game import BOARD_SIZE, voisins
    
    # Score de base: différence de jetons
    score_nous = compter_jetons(plateau, joueur_id)
    score_adversaire = compter_jetons(plateau, adversaire_id)
    score_base = score_nous - score_adversaire
    
    bonus_nous = 0
    malus_adversaire = 0
    
    # Analyser chaque cellule du plateau
    for x in range(BOARD_SIZE):
        for y in range(BOARD_SIZE):
            cell = plateau[x][y]
            
            # === CELLULES PRÊTES À EXPLOSER (3 jetons) ===
            # C'est CRUCIAL - avoir une cellule prête à exploser est très avantageux
            if cell.jeton == 3:
                if cell.joueur == joueur_id:
                    bonus_nous += 15  # Grand bonus si on peut exploser
                elif cell.joueur == adversaire_id:
                    malus_adversaire += 15  # Alerte: l'adversaire peut exploser!
            
            # === CELLULES À 2 JETONS ===
            # Proches de l'explosion, à surveiller
            elif cell.jeton == 2:
                if cell.joueur == joueur_id:
                    bonus_nous += 5
                elif cell.joueur == adversaire_id:
                    malus_adversaire += 5
            
            # === CELLULES CONTRÔLÉES ===
            # Bonus pour les zones défendues
            elif cell.jeton >= 1:
                if cell.joueur == joueur_id:
                    bonus_nous += 2
                elif cell.joueur == adversaire_id:
                    malus_adversaire += 2
    
    # === ANALYSE DES CHAÎNES D'EXPLOSION POTENTIELLES ===
    # Identifier les positions stratégiques qui pourraient trigger des explosions en cascade
    for x in range(BOARD_SIZE):
        for y in range(BOARD_SIZE):
            cell = plateau[x][y]
            
            if cell.jeton == 3 and cell.joueur != 0:
                joueur_cell = cell.joueur
                voisins_list = voisins(x, y)
                
                # Compter les voisins du même joueur
                voisins_memes = sum(
                    1 for nx, ny in voisins_list
                    if plateau[nx][ny].joueur == joueur_cell and plateau[nx][ny].jeton > 0
                )
                
                # Bonus additionnel si explosion en chaîne probable
                bonus_chaine = voisins_memes * 3
                
                if joueur_cell == joueur_id:
                    bonus_nous += bonus_chaine
                else:
                    malus_adversaire += bonus_chaine
    
    # === MENACES IMMINENTES DE L'ADVERSAIRE ===
    # Pénalité si l'adversaire a plusieurs cellules prêtes à exploser
    cellules_pret_exploser_adversaire = sum(
        1 for row in plateau for cell in row
        if cell.joueur == adversaire_id and cell.jeton == 3
    )
    if cellules_pret_exploser_adversaire > 1:
        malus_adversaire += cellules_pret_exploser_adversaire * 10
    
    # === SCORE FINAL COMBINÉ ===
    # Structure: Score brut + bonus - malus
    # Les cellules prêtes à exploser ont un poids TRÈS IMPORTANT
    score_final = score_base + bonus_nous - malus_adversaire
    
    return score_final


def minimax_alpha_beta(plateau, joueur_id, adversaire_id, profondeur, est_maximisant, 
                       alpha=float('-inf'), beta=float('inf'), autoriser_case_vide=False):
    """
    Algorithme Minimax avec élagage Alpha-Bêta (Alpha-Beta Pruning).
    
    Cette optimisation permet d'explorer beaucoup moins de positions en élaguant
    les branches qui ne peuvent pas influencer le résultat final.
    
    Concept:
    - alpha: Le meilleur score que le joueur maximisant peut garantir
    - beta: Le meilleur score que le joueur minimisant peut garantir
    - Si beta <= alpha, on peut élaguer la branche (pruning)
    
    Args:
        plateau: La grille de jeu (List[List[Cell]])
        joueur_id: ID du joueur pour lequel on calcule (1 ou 2)
        adversaire_id: ID de l'adversaire (l'autre joueur)
        profondeur: Profondeur restante à explorer (0 = condition d'arrêt)
        est_maximisant: True si c'est le tour du joueur (maximize), False si tour adversaire (minimize)
        alpha: Meilleur score pour le maximisant (initialement -inf)
        beta: Meilleur score pour le minimisant (initialement +inf)
        autoriser_case_vide: True si on peut jouer sur une case vide
    
    Returns:
        Tuple (meilleur_score, meilleur_coup)
    """
    global stats_elagage
    
    # ===== CONDITION D'ARRÊT =====
    # Quand profondeur = 0, on évalue la position et on retourne
    if profondeur == 0:
        score = evaluer_plateau(plateau, joueur_id, adversaire_id)
        return score, None
    
    # ===== VÉRIFICATION DU CACHE =====
    # Clé composée de : état du plateau + joueur actuel + profondeur + type de nœud (max/min)
    cle = (plateau_to_key(plateau), joueur_id, profondeur, est_maximisant)
    if cle in cache_arbre:
        return cache_arbre[cle]
    
    # ===== GÉNÉRATION DES COUPS =====
    joueur_actuel = joueur_id if est_maximisant else adversaire_id
    coups = coups_possibles(plateau, joueur_actuel)
    
    # Si pas de coups possibles, on évalue la position actuelle
    if not coups:
        score = evaluer_plateau(plateau, joueur_id, adversaire_id)
        result = (score, None)
        cache_arbre[cle] = result
        return result
    
    # ===== INITIALISATION =====
    meilleur_score = float('-inf') if est_maximisant else float('inf')
    meilleur_coup = None
    
    # ===== BOUCLE SUR TOUS LES COUPS =====
    for coup in coups:
        x, y = coup
        plateau_copie = deepcopy(plateau)
        
        # Jouer le coup sur une copie du plateau
        if jouer_coup(plateau_copie, x, y, joueur_actuel, autoriser_case_vide=autoriser_case_vide):
            stats_elagage["noeuds_explores"] += 1
            
            # ===== APPEL RÉCURSIF =====
            # Alternation entre maximisant et minimisant
            score, _ = minimax_alpha_beta(
                plateau_copie,
                joueur_id,
                adversaire_id,
                profondeur - 1,
                not est_maximisant,  # Alterne max/min
                alpha,
                beta,
                autoriser_case_vide=False
            )
            
            # ===== MISE À JOUR DES SCORES ET ALPHA-BÊTA =====
            if est_maximisant:
                # Nœud maximisant: on veut augmenter le score
                if score > meilleur_score:
                    meilleur_score = score
                    meilleur_coup = coup
                alpha = max(alpha, meilleur_score)
            else:
                # Nœud minimisant: on veut diminuer le score
                if score < meilleur_score:
                    meilleur_score = score
                    meilleur_coup = coup
                beta = min(beta, meilleur_score)
            
            # ===== ÉLAGAGE ALPHA-BÊTA =====
            # Si beta <= alpha, les branches suivantes ne changeront pas le résultat
            if beta <= alpha:
                stats_elagage["noeuds_elagues"] += 1
                break  # On coupe l'exploration des autres coups
    
    # ===== MISE EN CACHE ET RETOUR =====
    result = (meilleur_score, meilleur_coup)
    cache_arbre[cle] = result
    return result


def minimax_bot(plateau, joueur_id):
    """
    Fonction principale du bot qui utilise l'algorithme Minimax avec Alpha-Bêta Pruning.
    
    Cette fonction:
    1. Détecte si c'est le premier coup du joueur
    2. Appelle minimax_alpha_beta pour trouver le meilleur coup
    3. Joue le coup sur le plateau original
    
    Args:
        plateau: La grille de jeu (List[List[Cell]])
        joueur_id: ID du joueur (1 ou 2)
    
    Returns:
        True si un coup a été joué, False sinon
    """
    global stats_elagage
    
    # Réinitialiser les stats
    stats_elagage = {"noeuds_elagues": 0, "noeuds_explores": 0}
    
    # Calcul l'ID de l'adversaire (1 <-> 2)
    adversaire_id = 3 - joueur_id
    
    # Détecte si c'est le premier coup: vrai si le joueur n'a aucun jeton
    premier_coup = all(cell.joueur != joueur_id for row in plateau for cell in row)
    
    # Appelle l'algorithme minimax en mode maximisant (on cherche à maximiser)
    _, coup = minimax_alpha_beta(
        plateau,
        joueur_id,
        adversaire_id,
        profondeur_max,
        est_maximisant=True,
        alpha=float('-inf'),
        beta=float('inf'),
        autoriser_case_vide=premier_coup
    )
    
    # Afficher les stats d'élagage (optionnel)
    # print(f"Noeuds explorés: {stats_elagage['noeuds_explores']}, Noeuds élaguées: {stats_elagage['noeuds_elagues']}")
    
    # Joue le coup trouvé
    if coup:
        x, y = coup
        jouer_coup(plateau, x, y, joueur_id, autoriser_case_vide=premier_coup)
        return True
    return False


def vider_cache():
    """
    Réinitialise le cache global.
    
    À utiliser si vous voulez forcer le recalcul de toutes les positions
    (par exemple, au début d'une nouvelle partie).
    """
    global cache_arbre
    cache_arbre = {}


def afficher_stats_elagage():
    """
    Affiche les statistiques d'élagage alpha-bêta.
    
    Utile pour vérifier l'efficacité du pruning:
    - Si beaucoup de nœuds sont élaguées, c'est bon! On explore moins.
    - Si peu de nœuds sont élaguées, c'est que l'ordre des coups n'est pas optimal.
    """
    print(f"Nœuds explorés: {stats_elagage['noeuds_explores']}")
    print(f"Nœuds élaguées: {stats_elagage['noeuds_elagues']}")
    ratio = (stats_elagage['noeuds_elagues'] / max(1, stats_elagage['noeuds_explores'] + stats_elagage['noeuds_elagues'])) * 100
    print(f"Efficacité du pruning: {ratio:.1f}%")