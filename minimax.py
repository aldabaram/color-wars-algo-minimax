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
    Évalue la qualité du plateau pour le joueur actuel.
    
    Score = (nos jetons - jetons adversaire)
    Un score positif signifie qu'on a l'avantage.
    
    Args:
        plateau: La grille de jeu (List[List[Cell]])
        joueur_id: ID du joueur (1 ou 2)
        adversaire_id: ID de l'adversaire
    
    Returns:
        La différence de jetons (int)
    """
    score_nous = compter_jetons(plateau, joueur_id)
    score_adversaire = compter_jetons(plateau, adversaire_id)
    return score_nous - score_adversaire


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