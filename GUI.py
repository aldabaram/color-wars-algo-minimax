import pygame
import sys
import random
from game import (
    create_board, placer_jeton_initial, jouer_coup, 
    joueur_a_perdu, compter_jetons, BOARD_SIZE
)
from minimax import minimax_bot as minimax

# -----------------------
# CONFIGURATION
# -----------------------
TAILLE_CASE = 60
MARGE = 2
LARGEUR = BOARD_SIZE * TAILLE_CASE + 300  # Espace pour le panneau latéral
HAUTEUR = BOARD_SIZE * TAILLE_CASE

# Couleurs
COULEUR_BG = (25, 25, 35)
COULEUR_GRILLE = (50, 50, 65)
COULEUR_TEXTE = (220, 220, 230)
COULEUR_HOVER = (80, 80, 100)

COULEURS_JOUEURS = [
    (255, 70, 70),   # Rouge
    (70, 130, 255),  # Bleu
    (70, 255, 130),  # Vert
    (255, 215, 70),  # Jaune
]

# -----------------------
# CLASSE PRINCIPALE
# -----------------------
class ColorWarsGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((LARGEUR, HAUTEUR))
        pygame.display.set_caption("Color Wars")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        
        # État du jeu
        self.plateau = create_board()
        self.phase = "menu"  # menu, placement, jeu, game_over
        self.joueur_actuel = 1
        self.nb_joueurs = 2
        self.joueurs_info = []  # Liste de "humain" ou "bot"
        self.gagnant = None
        
        # Animation
        self.selected_case = None
        self.hover_case = None
        self.animation_time = 0
        self.pulse_offset = 0
        
        # Animation des rayons (pour transition fluide)
        self.rayons_actuels = {}  # {(x, y): rayon_actuel}
        self.rayons_cibles = {}   # {(x, y): rayon_cible}
        
        # Boutons du menu
        self.menu_buttons = []
        self.create_menu_buttons()
    
    def create_menu_buttons(self):
        """Crée les boutons du menu principal"""
        center_x = LARGEUR // 2
        start_y = 250
        
        self.menu_buttons = [
            {"text": "2 Joueurs", "rect": pygame.Rect(center_x - 100, start_y, 200, 50), "action": lambda: self.select_player_types(2)},
            {"text": "3 Joueurs", "rect": pygame.Rect(center_x - 100, start_y + 70, 200, 50), "action": lambda: self.select_player_types(3)},
            {"text": "4 Joueurs", "rect": pygame.Rect(center_x - 100, start_y + 140, 200, 50), "action": lambda: self.select_player_types(4)},
        ]
    
    def select_player_types(self, nb_joueurs):
        """Passe à la phase de sélection des types de joueurs"""
        self.nb_joueurs = nb_joueurs
        self.phase = "select_types"
        self.joueurs_info = ["humain"] * nb_joueurs  # Par défaut tous humains
        self.create_type_buttons()
    
    def create_type_buttons(self):
        """Crée les boutons pour choisir le type de chaque joueur"""
        self.type_buttons = []
        center_x = LARGEUR // 2
        start_y = 200
        
        for i in range(self.nb_joueurs):
            y_pos = start_y + i * 80
            
            # Bouton Humain
            humain_rect = pygame.Rect(center_x - 220, y_pos, 100, 50)
            # Bouton Bot
            bot_rect = pygame.Rect(center_x - 110, y_pos, 100, 50)
            
            self.type_buttons.append({
                "joueur": i,
                "humain": humain_rect,
                "bot": bot_rect
            })
        
        # Bouton Démarrer
        self.start_button = pygame.Rect(center_x - 100, start_y + self.nb_joueurs * 80 + 30, 200, 50)
    
    def toggle_player_type(self, joueur_idx, type_joueur):
        """Change le type d'un joueur"""
        self.joueurs_info[joueur_idx] = type_joueur
    
    def dessiner_selection_types(self):
        """Dessine l'écran de sélection des types de joueurs"""
        # Titre
        titre = self.font.render("CONFIGURATION", True, COULEUR_TEXTE)
        titre_rect = titre.get_rect(center=(LARGEUR // 2, 120))
        self.screen.blit(titre, titre_rect)
        
        mouse_pos = pygame.mouse.get_pos()
        
        # Boutons pour chaque joueur
        for i, button_group in enumerate(self.type_buttons):
            couleur_joueur = COULEURS_JOUEURS[i]
            
            # Label du joueur
            label = self.font_small.render(f"Joueur {i+1}:", True, couleur_joueur)
            label_rect = label.get_rect(center=(LARGEUR // 2 - 320, button_group["humain"].centery))
            self.screen.blit(label, label_rect)
            
            # Bouton Humain
            is_humain = self.joueurs_info[i] == "humain"
            is_hover_humain = button_group["humain"].collidepoint(mouse_pos)
            
            if is_humain:
                color_humain = (100, 150, 100)  # Vert si sélectionné
            elif is_hover_humain:
                color_humain = (80, 80, 120)
            else:
                color_humain = (60, 60, 90)
            
            pygame.draw.rect(self.screen, color_humain, button_group["humain"], border_radius=8)
            pygame.draw.rect(self.screen, COULEUR_TEXTE, button_group["humain"], 2, border_radius=8)
            
            text_humain = self.font_small.render("Humain", True, COULEUR_TEXTE)
            text_rect_humain = text_humain.get_rect(center=button_group["humain"].center)
            self.screen.blit(text_humain, text_rect_humain)
            
            # Bouton Bot
            is_bot = self.joueurs_info[i] == "bot"
            is_hover_bot = button_group["bot"].collidepoint(mouse_pos)
            
            if is_bot:
                color_bot = (100, 150, 100)  # Vert si sélectionné
            elif is_hover_bot:
                color_bot = (80, 80, 120)
            else:
                color_bot = (60, 60, 90)
            
            pygame.draw.rect(self.screen, color_bot, button_group["bot"], border_radius=8)
            pygame.draw.rect(self.screen, COULEUR_TEXTE, button_group["bot"], 2, border_radius=8)
            
            text_bot = self.font_small.render("Bot", True, COULEUR_TEXTE)
            text_rect_bot = text_bot.get_rect(center=button_group["bot"].center)
            self.screen.blit(text_bot, text_rect_bot)
        
        # Bouton Démarrer
        is_hover_start = self.start_button.collidepoint(mouse_pos)
        color_start = (80, 150, 80) if is_hover_start else (60, 120, 60)
        
        pygame.draw.rect(self.screen, color_start, self.start_button, border_radius=10)
        pygame.draw.rect(self.screen, COULEUR_TEXTE, self.start_button, 2, border_radius=10)
        
        text_start = self.font.render("DÉMARRER", True, COULEUR_TEXTE)
        text_rect_start = text_start.get_rect(center=self.start_button.center)
        self.screen.blit(text_start, text_rect_start)
    
    def traiter_clic_selection_types(self, pos):
        """Gère les clics dans l'écran de sélection de types"""
        # Vérifier les boutons de type
        for button_group in self.type_buttons:
            if button_group["humain"].collidepoint(pos):
                self.toggle_player_type(button_group["joueur"], "humain")
                return
            elif button_group["bot"].collidepoint(pos):
                self.toggle_player_type(button_group["joueur"], "bot")
                return
        
        # Vérifier le bouton démarrer
        if self.start_button.collidepoint(pos):
            self.start_game()
    
    def start_game(self):
        """Démarre une nouvelle partie"""
        self.plateau = create_board()
        self.joueur_actuel = 1
        self.phase = "placement"
    
    def get_case_from_mouse(self, pos):
        """Convertit position souris en coordonnées plateau"""
        x, y = pos
        case_x, case_y = x // TAILLE_CASE, y // TAILLE_CASE
        if 0 <= case_x < BOARD_SIZE and 0 <= case_y < BOARD_SIZE:
            return case_x, case_y
        return None
    
    def dessiner_grille(self):
        """Dessine la grille du plateau"""
        for x in range(BOARD_SIZE):
            for y in range(BOARD_SIZE):
                rect = pygame.Rect(
                    x * TAILLE_CASE, y * TAILLE_CASE, 
                    TAILLE_CASE, TAILLE_CASE
                )
                
                # Effet hover
                if self.hover_case == (x, y):
                    pygame.draw.rect(self.screen, COULEUR_HOVER, rect)
                
                pygame.draw.rect(self.screen, COULEUR_GRILLE, rect, MARGE)
    
    def dessiner_jetons(self):
        """Dessine les jetons avec animations fluides"""
        for x in range(BOARD_SIZE):
            for y in range(BOARD_SIZE):
                cell = self.plateau[x][y]
                if cell.joueur == 0:
                    continue
                
                couleur = COULEURS_JOUEURS[cell.joueur - 1]
                
                # Calcul du rayon cible
                rayon_cible = 10 + cell.jeton * 6
                
                # Animation fluide du rayon
                pos = (x, y)
                if pos not in self.rayons_actuels:
                    self.rayons_actuels[pos] = rayon_cible
                    self.rayons_cibles[pos] = rayon_cible
                
                if self.rayons_cibles[pos] != rayon_cible:
                    self.rayons_cibles[pos] = rayon_cible
                
                # Interpolation fluide vers le rayon cible
                if abs(self.rayons_actuels[pos] - self.rayons_cibles[pos]) > 0.5:
                    self.rayons_actuels[pos] += (self.rayons_cibles[pos] - self.rayons_actuels[pos]) * 0.2
                else:
                    self.rayons_actuels[pos] = self.rayons_cibles[pos]
                
                rayon = int(self.rayons_actuels[pos])
                
                center_x = x * TAILLE_CASE + TAILLE_CASE // 2
                center_y = y * TAILLE_CASE + TAILLE_CASE // 2
                
                # Jeton simple - juste un rond
                pygame.draw.circle(self.screen, couleur, 
                                 (center_x, center_y), rayon)
                
                # Nombre de jetons
                text = self.font_small.render(str(cell.jeton), True, (255, 255, 255))
                text_rect = text.get_rect(center=(center_x, center_y))
                self.screen.blit(text, text_rect)
        
        # Nettoyer les rayons des cases qui n'ont plus de jetons
        positions_a_supprimer = []
        for pos in self.rayons_actuels:
            x, y = pos
            if self.plateau[x][y].joueur == 0:
                positions_a_supprimer.append(pos)
        
        for pos in positions_a_supprimer:
            del self.rayons_actuels[pos]
            del self.rayons_cibles[pos]
    
    def dessiner_panneau_lateral(self):
        """Dessine le panneau d'information latéral"""
        panel_x = BOARD_SIZE * TAILLE_CASE
        
        # Fond du panneau
        panel_rect = pygame.Rect(panel_x, 0, 300, HAUTEUR)
        pygame.draw.rect(self.screen, (35, 35, 50), panel_rect)
        
        # Titre
        y_offset = 20
        if self.phase == "placement":
            titre = "PLACEMENT"
        elif self.phase == "jeu":
            titre = "EN JEU"
        else:
            titre = "GAME OVER"
        
        text = self.font.render(titre, True, COULEUR_TEXTE)
        self.screen.blit(text, (panel_x + 20, y_offset))
        y_offset += 60
        
        # Affichage du gagnant
        if self.phase == "game_over" and self.gagnant:
            couleur_gagnant = COULEURS_JOUEURS[self.gagnant - 1]
            text = self.font.render(f"Joueur {self.gagnant}", True, couleur_gagnant)
            self.screen.blit(text, (panel_x + 20, y_offset))
            y_offset += 40
            text = self.font_small.render("a gagné !", True, COULEUR_TEXTE)
            self.screen.blit(text, (panel_x + 20, y_offset))
            y_offset += 60
        
        # Info joueur actuel
        if self.phase in ["placement", "jeu"]:
            couleur = COULEURS_JOUEURS[self.joueur_actuel - 1]
            text = self.font_small.render(f"Joueur {self.joueur_actuel}", True, couleur)
            self.screen.blit(text, (panel_x + 20, y_offset))
            y_offset += 40
            
            # Type de joueur
            type_joueur = self.joueurs_info[self.joueur_actuel - 1]
            text = self.font_small.render(f"({type_joueur})", True, COULEUR_TEXTE)
            self.screen.blit(text, (panel_x + 20, y_offset))
            y_offset += 50
        
        # Statistiques
        text = self.font_small.render("STATISTIQUES", True, COULEUR_TEXTE)
        self.screen.blit(text, (panel_x + 20, y_offset))
        y_offset += 35
        
        for i in range(1, len(self.joueurs_info) + 1):
            couleur = COULEURS_JOUEURS[i - 1]
            jetons = compter_jetons(self.plateau, i)
            
            # Marquer les joueurs éliminés
            if joueur_a_perdu(self.plateau, i):
                text = self.font_small.render(f"J{i}: ÉLIMINÉ", True, (100, 100, 100))
            else:
                text = self.font_small.render(f"J{i}: {jetons} jetons", True, couleur)
            self.screen.blit(text, (panel_x + 30, y_offset))
            y_offset += 30
        
        # Instructions
        y_offset = HAUTEUR - 100
        text = self.font_small.render("ESC - Menu", True, COULEUR_TEXTE)
        self.screen.blit(text, (panel_x + 20, y_offset))
    
    def dessiner_menu(self):
        """Dessine le menu principal"""
        # Titre
        titre = self.font.render("COLOR WARS", True, COULEUR_TEXTE)
        titre_rect = titre.get_rect(center=(LARGEUR // 2, 150))
        self.screen.blit(titre, titre_rect)
        
        # Boutons
        mouse_pos = pygame.mouse.get_pos()
        for button in self.menu_buttons:
            # Effet hover
            is_hover = button["rect"].collidepoint(mouse_pos)
            color = (80, 80, 120) if is_hover else (60, 60, 90)
            
            pygame.draw.rect(self.screen, color, button["rect"], border_radius=10)
            pygame.draw.rect(self.screen, COULEUR_TEXTE, button["rect"], 2, border_radius=10)
            
            # Texte
            text = self.font_small.render(button["text"], True, COULEUR_TEXTE)
            text_rect = text.get_rect(center=button["rect"].center)
            self.screen.blit(text, text_rect)
    
    def traiter_clic_menu(self, pos):
        """Gère les clics dans le menu"""
        for button in self.menu_buttons:
            if button["rect"].collidepoint(pos):
                button["action"]()
                return
    
    def traiter_clic_plateau(self, case):
        """Gère les clics sur le plateau"""
        x, y = case
        self.selected_case = (x, y)
        
        if self.phase == "placement":
            # Pendant le placement, on ne peut placer que sur des cases vides
            if self.plateau[x][y].joueur == 0:
                if placer_jeton_initial(self.plateau, x, y, self.joueur_actuel):
                    self.joueur_actuel += 1
                    if self.joueur_actuel > len(self.joueurs_info):
                        self.phase = "jeu"
                        self.joueur_actuel = 1
                    
        elif self.phase == "jeu":
            # Vérifier que le joueur n'est pas éliminé
            if joueur_a_perdu(self.plateau, self.joueur_actuel):
                self.joueur_suivant()
                return
            
            # Pendant le jeu, on ne peut jouer que sur ses propres cases
            if jouer_coup(self.plateau, x, y, self.joueur_actuel, autoriser_case_vide=False):
                # Vérifier victoire
                self.verifier_victoire()
                # Passer au joueur suivant
                self.joueur_suivant()
    
    def joueur_suivant(self):
        """Passe au joueur suivant en sautant les joueurs éliminés"""
        tours_passes = 0
        max_tours = len(self.joueurs_info)
        
        while tours_passes < max_tours:
            self.joueur_actuel += 1
            if self.joueur_actuel > len(self.joueurs_info):
                self.joueur_actuel = 1
            
            # Si le joueur n'est pas éliminé, on s'arrête
            if not joueur_a_perdu(self.plateau, self.joueur_actuel):
                break
            
            tours_passes += 1
        
        # Si tous les joueurs sont éliminés sauf un, c'est déjà géré par verifier_victoire
    
    def verifier_victoire(self):
        """Vérifie si un joueur a gagné"""
        joueurs_en_vie = []
        for i in range(1, len(self.joueurs_info) + 1):
            if not joueur_a_perdu(self.plateau, i):
                joueurs_en_vie.append(i)
        
        if len(joueurs_en_vie) == 1:
            self.gagnant = joueurs_en_vie[0]
            self.phase = "game_over"
    
    def traiter_tour_bot(self):
        """Fait jouer le bot"""
        if self.phase == "placement":
            # Placement aléatoire
            while True:
                x = random.randint(0, BOARD_SIZE - 1)
                y = random.randint(0, BOARD_SIZE - 1)
                if placer_jeton_initial(self.plateau, x, y, self.joueur_actuel):
                    self.joueur_actuel += 1
                    if self.joueur_actuel > len(self.joueurs_info):
                        self.phase = "jeu"
                        self.joueur_actuel = 1
                    break
        
        elif self.phase == "jeu":
            # Vérifier que le bot n'est pas éliminé
            if joueur_a_perdu(self.plateau, self.joueur_actuel):
                self.joueur_suivant()
                return
            
            if minimax(self.plateau, self.joueur_actuel):
                self.verifier_victoire()
                self.joueur_suivant()
    
    def run(self):
        """Boucle principale du jeu"""
        running = True
        bot_timer = 0
        
        while running:
            dt = self.clock.tick(60) / 1000.0  # Delta time en secondes
            self.animation_time += dt
            
            # Gestion des événements
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.phase = "menu"
                        self.create_menu_buttons()
                
                elif event.type == pygame.MOUSEMOTION:
                    if self.phase in ["placement", "jeu"]:
                        self.hover_case = self.get_case_from_mouse(event.pos)
                
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.phase == "menu":
                        self.traiter_clic_menu(event.pos)
                    elif self.phase == "select_types":
                        self.traiter_clic_selection_types(event.pos)
                    elif self.phase in ["placement", "jeu"]:
                        case = self.get_case_from_mouse(event.pos)
                        if case:
                            self.traiter_clic_plateau(case)
            
            # Tour du bot
            if self.phase in ["placement", "jeu"]:
                if self.joueurs_info[self.joueur_actuel - 1] == "bot":
                    bot_timer += dt
                    if bot_timer > 0.5:  # Délai de 0.5s pour le bot
                        self.traiter_tour_bot()
                        bot_timer = 0
            
            # Rendu
            self.screen.fill(COULEUR_BG)
            
            if self.phase == "menu":
                self.dessiner_menu()
            elif self.phase == "select_types":
                self.dessiner_selection_types()
            else:
                self.dessiner_grille()
                self.dessiner_jetons()
                self.dessiner_panneau_lateral()
            
            pygame.display.flip()
        
        pygame.quit()
        sys.exit()