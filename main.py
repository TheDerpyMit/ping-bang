import pygame
import sys
import os
import time
from pygame import gfxdraw
from menu import Menu
from game import Game

# Initialize Pygame and mixer
pygame.init()
pygame.mixer.init()

# Constants
WINDOW_WIDTH = 960
WINDOW_HEIGHT = 540
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (40, 40, 40)
ACCENT = (0, 255, 200)

class PingPong:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("mit's ping bang")
        self.clock = pygame.time.Clock()
        
        # Make sure cursor starts visible
        pygame.mouse.set_visible(True)
        
        # Create assets directory if it doesn't exist
        if not os.path.exists('assets'):
            os.makedirs('assets')
            
        # Initialize states
        self.menu = Menu(self.screen)
        self.game = Game(self.screen, ai_difficulty="easy")
        self.current_state = "menu"
        
        # Load and play background music
        try:
            pygame.mixer.music.load('assets/background_music.wav')
            pygame.mixer.music.play(-1)
            # Set initial music volume based on settings
            if self.menu.settings.current_settings['music_enabled']:
                pygame.mixer.music.set_volume(1.0)  # Set music volume to 1.0
            else:
                pygame.mixer.music.set_volume(0.0)
        except:
            print("Background music file not found")
            
        # Load lose sound
        try:
            self.lose_sound = pygame.mixer.Sound('assets/lose.wav')
            self.lose_sound.set_volume(1.0)
        except:
            print("Lose sound file not found")
            self.lose_sound = None
            
    def fade_out(self, duration=1.0):
        """Fade out the screen to black and fade out the music"""
        # Create a black surface for fading
        fade_surface = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        fade_surface.fill(BLACK)
        
        # Get initial music volume
        initial_volume = pygame.mixer.music.get_volume()
        
        # Calculate steps for smooth fade
        steps = int(duration * FPS)
        alpha_step = 255 / steps
        volume_step = initial_volume / steps
        
        # Capture the current screen
        current_screen = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        current_screen.blit(self.screen, (0, 0))
        
        # Fade out animation
        for i in range(steps + 1):
            # Calculate current alpha and volume
            alpha = min(255, int(alpha_step * i))
            volume = max(0, initial_volume - (volume_step * i))
            
            # Set music volume
            pygame.mixer.music.set_volume(volume)
            
            # Draw the current screen
            self.screen.blit(current_screen, (0, 0))
            
            # Set alpha for the fade surface
            fade_surface.set_alpha(alpha)
            
            # Draw the fade surface
            self.screen.blit(fade_surface, (0, 0))
            
            # Update the display
            pygame.display.flip()
            
            # Control the frame rate
            self.clock.tick(FPS)
            
        # Play lose sound if available
        if self.lose_sound:
            self.lose_sound.play()
            # Wait for the sound to finish
            pygame.time.wait(int(self.lose_sound.get_length() * 1000))
            
        # Ensure music is completely stopped
        pygame.mixer.music.stop()

    def run(self):
        while True:
            if self.current_state == "menu":
                result = self.menu.run()
                if result == "quit":
                    break
                elif result.startswith("game:"):
                    self.current_state = "game"
                    self.game = Game(self.screen, ai_difficulty=result.split(":")[1])
                elif result == "scores":
                    self.current_state = "scores"
            elif self.current_state == "game":
                result = self.game.run()
                if result == "quit":
                    break
                elif result == "menu":
                    self.current_state = "menu"
                elif result.startswith("scores:"):
                    score = int(result.split(":")[1])
                    self.current_state = "scores"
                    result = self.menu.run_global_scores_menu(score)
                    if result == "quit":
                        break
                    elif result == "back":
                        self.current_state = "menu"
            elif self.current_state == "scores":
                result = self.menu.run_global_scores_menu()
                if result == "quit":
                    break
                elif result == "back":
                    self.current_state = "menu"
            elif self.current_state == "fullscreen_toggle":
                # Handle fullscreen toggle at the main game level
                pygame.display.toggle_fullscreen()
                # Update screen reference for all components
                self.screen = pygame.display.get_surface()
                # Reinitialize menu and game with new screen dimensions
                self.menu = Menu(self.screen)
                if hasattr(self, 'game'):
                    # Preserve game state if it exists
                    difficulty = self.game.paddle_right.ai_difficulty
                    self.game = Game(self.screen, ai_difficulty=difficulty)

            pygame.display.flip()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = PingPong()
    game.run() 