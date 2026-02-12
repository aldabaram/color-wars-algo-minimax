from random import choice
from copy import deepcopy
from game import coups_possibles, jouer_coup, compter_jetons

profondeur_max = 2

# Cache pour mémoriser les branches déjà calculées
cache_arbre = {}

def plateau_to_key(plateau):
    """Convertit le plateau en clé hashable pour le cache"""
    return tuple(
        tuple((cell.joueur, cell.jeton) for cell in row)
        for row in plateau
    )

def evaluer_plateau(plateau, joueur_id, adversaire_id):
    """Évalue le plateau : différence de jetons (nous - adversaire)"""
    score_nous = compter_jetons(plateau, joueur_id)
    score_adversaire = compter_jetons(plateau, adversaire_id)
    return score_nous - score_adversaire

def minimax(plateau, joueur_id, adversaire_id, profondeur, est_maximisant, autoriser_case_vide=False):
    """
    Algorithme Minimax : retourne (meilleur_score, meilleur_coup)
    - est_maximisant=True : on cherche à maximiser (notre tour)
    - est_maximisant=False : on cherche à minimiser (tour adversaire)
    """
    # Condition d'arrêt
    if profondeur == 0:
        score = evaluer_plateau(plateau, joueur_id, adversaire_id)
        return score, None
    
    # Vérifier le cache
    cle = (plateau_to_key(plateau), joueur_id, profondeur, est_maximisant)
    if cle in cache_arbre:
        return cache_arbre[cle]
    
    joueur_actuel = joueur_id if est_maximisant else adversaire_id
    coups = coups_possibles(plateau, joueur_actuel)
    
    if not coups:
        score = evaluer_plateau(plateau, joueur_id, adversaire_id)
        result = (score, None)
        cache_arbre[cle] = result
        return result
    
    meilleur_score = float('-inf') if est_maximisant else float('inf')
    meilleur_coup = None
    
    for coup in coups:
        x, y = coup
        plateau_copie = deepcopy(plateau)
        
        # Jouer le coup
        if jouer_coup(plateau_copie, x, y, joueur_actuel, autoriser_case_vide=autoriser_case_vide):
            # Appel récursif avec alternance min/max
            score, _ = minimax(
                plateau_copie,
                joueur_id,
                adversaire_id,
                profondeur - 1,
                not est_maximisant,  # Alterne max/min
                autoriser_case_vide=False
            )
            
            # Mettre à jour le meilleur score
            if est_maximisant:
                if score > meilleur_score:
                    meilleur_score = score
                    meilleur_coup = coup
            else:
                if score < meilleur_score:
                    meilleur_score = score
                    meilleur_coup = coup
    
    result = (meilleur_score, meilleur_coup)
    cache_arbre[cle] = result
    return result

def minimax_bot(plateau, joueur_id):
    """Bot utilisant l'algorithme Minimax avec cache"""
    adversaire_id = 3 - joueur_id  # Si joueur_id=1 alors adversaire=2, etc.
    
    # Vérifier si c'est le premier coup du joueur
    premier_coup = all(cell.joueur != joueur_id for row in plateau for cell in row)
    
    # Lancer minimax en mode maximisant
    _, coup = minimax(
        plateau,
        joueur_id,
        adversaire_id,
        profondeur_max,
        est_maximisant=True,
        autoriser_case_vide=premier_coup
    )
    
    if coup:
        x, y = coup
        jouer_coup(plateau, x, y, joueur_id, autoriser_case_vide=premier_coup)
        return True
    return False

def vider_cache():
    """Réinitialise le cache (à appeler si nécessaire)"""
    global cache_arbre
    cache_arbre = {}