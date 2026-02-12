from dataclasses import dataclass
from typing import List, Tuple, Optional

# -----------------------
# CONFIGURATION
# -----------------------
BOARD_SIZE = 10
INITIAL_JETON = 3

@dataclass
class Cell:
    joueur: int = 0
    jeton: int = 0

Plateau = List[List[Cell]]

# -----------------------
# CRÉATION DU PLATEAU
# -----------------------
def create_board(size: int = BOARD_SIZE) -> Plateau:
    return [[Cell() for _ in range(size)] for _ in range(size)]

# -----------------------
# OUTILS INTERNES
# -----------------------
def voisins(x: int, y: int) -> List[Tuple[int, int]]:
    """Retourne les voisins orthogonaux d'une case"""
    return [
        (nx, ny)
        for nx, ny in [(x-1, y), (x+1, y), (x, y-1), (x, y+1)]
        if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE
    ]

def coups_possibles(plateau: Plateau, joueur: int) -> List[Tuple[int, int]]:
    """Retourne la liste des coups possibles pour un joueur"""
    coups = []
    for x in range(BOARD_SIZE):
        for y in range(BOARD_SIZE):
            if plateau[x][y].joueur in (0, joueur):
                coups.append((x, y))
    return coups

# -----------------------
# MÉCANIQUES DU JEU
# -----------------------
def explosion(plateau: Plateau, x: int, y: int, joueur: int) -> List[Tuple[int, int]]:
    """Gère l'explosion en chaîne et retourne les cases affectées pour l'animation"""
    cases_affectees = []
    pile = [(x, y)]
    
    while pile:
        cx, cy = pile.pop()
        for nx, ny in voisins(cx, cy):
            cell = plateau[nx][ny]
            cell.joueur = joueur
            cell.jeton += 1
            cases_affectees.append((nx, ny))
            
            if cell.jeton >= 4:
                cell.jeton = 0
                cell.joueur = 0
                pile.append((nx, ny))
    
    return cases_affectees

def jouer_coup(
    plateau: Plateau,
    x: int,
    y: int,
    joueur: int,
    autoriser_case_vide: bool = False
) -> bool:
    """Joue un coup et retourne True si valide"""
    cell = plateau[x][y]

    if cell.joueur not in (0, joueur):
        return False

    if cell.joueur == 0 and not autoriser_case_vide:
        return False

    if cell.joueur == 0:
        cell.joueur = joueur
        cell.jeton = 1
        return True

    cell.jeton += 1
    if cell.jeton >= 4:
        cell.jeton = 0
        cell.joueur = 0
        explosion(plateau, x, y, joueur)

    return True

def placer_jeton_initial(plateau: Plateau, x: int, y: int, joueur: int) -> bool:
    """Place le jeton initial d'un joueur"""
    cell = plateau[x][y]
    if cell.joueur != 0:
        return False
    cell.joueur = joueur
    cell.jeton = INITIAL_JETON
    return True

def joueur_a_perdu(plateau: Plateau, joueur: int) -> bool:
    """Vérifie si un joueur n'a plus de jetons"""
    return all(
        cell.joueur != joueur
        for row in plateau
        for cell in row
    )

def compter_jetons(plateau: Plateau, joueur: int) -> int:
    """Compte le nombre total de jetons d'un joueur"""
    return sum(
        cell.jeton
        for row in plateau
        for cell in row
        if cell.joueur == joueur
    )