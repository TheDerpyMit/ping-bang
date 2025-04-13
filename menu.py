import pygame
import sys
import json
import os
import platform
import requests
from pygame import gfxdraw
import datetime


COLOR_SCHEMES = {
    "EASY": {
        "background": [(220, 245, 255), (180, 225, 250)],
        "button": (240, 250, 255),
        "button_border": (190, 220, 240),
        "text": (30, 30, 30),
        "shadow": (160, 200, 220)
    },
    "MEDIUM": {
        "background": [(255, 190, 100), (240, 140, 60)],
        "button": (255, 160, 80),
        "button_border": (210, 110, 50),
        "text": (40, 20, 0),
        "shadow": (180, 100, 60)
    },
    "HARD": {
        "background": [(90, 0, 10), (150, 0, 30)],
        "button": (180, 30, 50),
        "button_border": (100, 0, 20),
        "text": (255, 230, 230),
        "shadow": (60, 0, 20)
    }
}


DISCORD_WEBHOOK_URL = "nuh uh"

class TextBox:
    def __init__(self, x, y, width, height, font_size=24, color_scheme=None, max_chars=200):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = ""
        self.font = pygame.font.Font(None, font_size)
        self.active = False
        self.color_scheme = color_scheme or COLOR_SCHEMES["EASY"]
        self.cursor_visible = True
        self.cursor_timer = 0
        self.cursor_blink_speed = 500  # milliseconds
        self.text_color = (0, 0, 0)  # Set default text color to black
        self.background_color = (255, 255, 255)
        self.border_color = self.color_scheme["button_border"]
        self.placeholder_text = "Describe the bug here..."
        self.placeholder_color = (150, 150, 150)
        self.wrapped_lines = []
        self.scroll_position = 0
        self.max_scroll = 0
        self.line_height = font_size + 4
        self.padding = 10
        self.last_time = pygame.time.get_ticks()
        self.max_chars = max_chars
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = True
            else:
                self.active = False
                
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                self.active = False
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_TAB:
                self.active = False
            else:
                # Only add printable characters and respect character limit
                if event.unicode.isprintable() and len(self.text) < self.max_chars:
                    self.text += event.unicode
                    
        # Update wrapped lines when text changes
        self.update_wrapped_lines()
        
    def update_wrapped_lines(self):
        if not self.text:
            self.wrapped_lines = [self.placeholder_text]
            return
            
        # Calculate the maximum width for text wrapping
        max_width = self.rect.width - 2 * self.padding
        
        # Split text into words
        words = self.text.split(' ')
        self.wrapped_lines = []
        current_line = []
        
        for word in words:
            # Test if adding this word would exceed the width
            test_line = ' '.join(current_line + [word])
            text_surface = self.font.render(test_line, True, self.text_color)
            
            if text_surface.get_width() <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    self.wrapped_lines.append(' '.join(current_line))
                # If the word itself is too long, we need to split it
                if self.font.render(word, True, self.text_color).get_width() > max_width:
                    # Split the word into characters
                    chars = list(word)
                    current_chars = []
                    for char in chars:
                        test_chars = ''.join(current_chars + [char])
                        if self.font.render(test_chars, True, self.text_color).get_width() <= max_width:
                            current_chars.append(char)
                        else:
                            if current_chars:
                                self.wrapped_lines.append(''.join(current_chars))
                            current_chars = [char]
                    if current_chars:
                        self.wrapped_lines.append(''.join(current_chars))
                else:
                    current_line = [word]
                
        if current_line:
            self.wrapped_lines.append(' '.join(current_line))
            
        # Calculate max scroll
        visible_lines = (self.rect.height - 2 * self.padding) // self.line_height
        self.max_scroll = max(0, len(self.wrapped_lines) - visible_lines)
        
        # Ensure scroll position is valid
        self.scroll_position = min(self.scroll_position, self.max_scroll)
        
    def draw(self, screen):
        # Draw the text box background
        pygame.draw.rect(screen, self.background_color, self.rect, border_radius=10)
        pygame.draw.rect(screen, self.border_color, self.rect, border_radius=10, width=2)
        
        # Create a clipping rectangle for the text area
        clip_rect = pygame.Rect(
            self.rect.x + self.padding,
            self.rect.y + self.padding,
            self.rect.width - 2 * self.padding,
            self.rect.height - 2 * self.padding
        )
        
        # Save the current clipping rectangle
        old_clip = screen.get_clip()
        
        # Set the clipping rectangle
        screen.set_clip(clip_rect)
        
        # Draw the text
        visible_lines = (self.rect.height - 2 * self.padding) // self.line_height
        start_line = self.scroll_position
        end_line = min(start_line + visible_lines, len(self.wrapped_lines))
        
        for i, line in enumerate(self.wrapped_lines[start_line:end_line]):
            if not self.text and i == 0:
                # Draw placeholder text
                text = self.font.render(line, True, self.placeholder_color)
            else:
                text = self.font.render(line, True, self.text_color)
                
            screen.blit(text, (self.rect.x + self.padding, 
                              self.rect.y + self.padding + i * self.line_height))
            
        # Restore the original clipping rectangle
        screen.set_clip(old_clip)
        
        # Draw cursor if active
        if self.active:
            self.cursor_timer += pygame.time.get_ticks() - self.last_time
            if self.cursor_timer >= self.cursor_blink_speed:
                self.cursor_visible = not self.cursor_visible
                self.cursor_timer = 0
                
            if self.cursor_visible:
                # Calculate cursor position
                if self.text:
                    cursor_text = self.text[:len(self.text)]
                    cursor_surface = self.font.render(cursor_text, True, self.text_color)
                    cursor_x = self.rect.x + self.padding + cursor_surface.get_width()
                else:
                    cursor_x = self.rect.x + self.padding
                    
                cursor_y = self.rect.y + self.padding
                pygame.draw.line(screen, self.text_color, 
                                (cursor_x, cursor_y), 
                                (cursor_x, cursor_y + self.font.get_height()))
        
        # Draw character count
        char_count_font = pygame.font.Font(None, 20)
        char_count_text = f"{len(self.text)}/{self.max_chars}"
        char_count_surface = char_count_font.render(char_count_text, True, (100, 100, 100))
        char_count_rect = char_count_surface.get_rect(right=self.rect.right - 10, bottom=self.rect.bottom - 5)
        screen.blit(char_count_surface, char_count_rect)
                
        self.last_time = pygame.time.get_ticks()
        
    def get_text(self):
        return self.text

class Button:
    def __init__(self, x, y, width, height, text, font_size=32, sound_file=None, color_scheme=None, icon=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.Font(None, font_size)
        self.color = (40, 40, 40)
        self.hover_color = (60, 60, 60)
        self.text_color = (0, 0, 0)
        self.is_hovered = False
        self.animation_progress = 0
        self.original_rect = pygame.Rect(x, y, width, height)
        self.scale = 1.0
        self.hover_offset = 0
        self.sound_file = sound_file
        self.hover_sound = None
        self.click_sound = None
        self.color_scheme = color_scheme
        self.transition_progress = 0
        self.target_color_scheme = color_scheme
        self.icon = icon
        self.load_sounds()
        
    def load_sounds(self):
        # hover sound for all buttons
        try:
            self.hover_sound = pygame.mixer.Sound('assets/hover.wav')
            self.hover_sound.set_volume(1.0)
        except:
            print(f"Hover sound file not found")
            
        if self.sound_file:
            try:
                self.click_sound = pygame.mixer.Sound(self.sound_file)
                self.click_sound.set_volume(1.0) 
            except:
                print(f"Click sound file {self.sound_file} not found")
    
    def set_color_scheme(self, new_scheme):

        self.target_color_scheme = new_scheme
        self.transition_progress = 0
    
    def update_transition(self, speed=0.01):

        if self.transition_progress < 1.0:
            self.transition_progress = min(1.0, self.transition_progress + speed)
            return True
        return False
        
    def draw(self, screen):
        self.update_transition()
        
        # Smooth hover animation
        if self.is_hovered:
            self.animation_progress = min(1, self.animation_progress + 0.08)
        else:
            self.animation_progress = max(0, self.animation_progress - 0.08)
            
        self.scale = 1.0 + (0.08 * self.animation_progress)
        scaled_width = int(self.original_rect.width * self.scale)
        scaled_height = int(self.original_rect.height * self.scale)
        
        self.hover_offset = -6 * self.animation_progress
        
        self.rect.width = scaled_width
        self.rect.height = scaled_height
        self.rect.centerx = self.original_rect.centerx
        self.rect.centery = self.original_rect.centery + self.hover_offset
        
        if self.color_scheme and self.target_color_scheme:
            button_color = self.interpolate_color(
                self.color_scheme["button"], 
                self.target_color_scheme["button"], 
                self.transition_progress
            )
            button_border = self.interpolate_color(
                self.color_scheme["button_border"], 
                self.target_color_scheme["button_border"], 
                self.transition_progress
            )
            text_color = self.interpolate_color(
                self.color_scheme["text"], 
                self.target_color_scheme["text"], 
                self.transition_progress
            )
            shadow_color = self.interpolate_color(
                self.color_scheme["shadow"], 
                self.target_color_scheme["shadow"], 
                self.transition_progress
            )
        else:
            # Default colors
            button_color = (255, 255, 255)
            button_border = (230, 230, 230)
            text_color = (0, 0, 0)
            shadow_color = (200, 200, 200)
        
        # shadow effect
        shadow_offset = int(6 * self.animation_progress)
        shadow_rect = self.rect.copy()
        shadow_rect.x += shadow_offset
        shadow_rect.y += shadow_offset
        pygame.draw.rect(screen, shadow_color, shadow_rect, border_radius=15)
        
        # draw button with animation
        pygame.draw.rect(screen, button_color, self.rect, border_radius=15)
        pygame.draw.rect(screen, button_border, self.rect, border_radius=15, width=2)
        
        # draw text with shadow
        if self.icon:
            # Draw icon instead of text
            icon_size = min(self.rect.width, self.rect.height) * 0.6
            icon_rect = pygame.Rect(0, 0, icon_size, icon_size)
            icon_rect.center = self.rect.center
            
            if self.icon == "i":
                # Draw information icon
                pygame.draw.circle(screen, text_color, icon_rect.center, icon_size/2, 2)
                info_text = self.font.render("i", True, text_color)
                info_rect = info_text.get_rect(center=icon_rect.center)
                screen.blit(info_text, info_rect)
            elif self.icon == "?":
                # Draw question mark icon
                pygame.draw.circle(screen, text_color, icon_rect.center, icon_size/2, 2)
                question_mark = self.font.render("?", True, text_color)
                question_rect = question_mark.get_rect(center=icon_rect.center)
                screen.blit(question_mark, question_rect)
            elif self.icon == "🏆":
                # Draw trophy icon
                trophy_text = self.font.render("🏆", True, text_color)
                trophy_rect = trophy_text.get_rect(center=icon_rect.center)
                screen.blit(trophy_text, trophy_rect)
        else:
            text_shadow = self.font.render(self.text, True, (150, 150, 150))
            text_surface = self.font.render(self.text, True, text_color)
            text_rect = text_surface.get_rect(center=self.rect.center)
            shadow_text_rect = text_rect.copy()
            shadow_text_rect.x += 2
            shadow_text_rect.y += 2
            screen.blit(text_shadow, shadow_text_rect)
            screen.blit(text_surface, text_rect)
    
    def interpolate_color(self, color1, color2, progress):

        # apply cubic easing to the progress for smoother transitions
        eased_progress = progress * progress * (3 - 2 * progress)
        
        r1, g1, b1 = color1
        r2, g2, b2 = color2
        r = int(r1 + (r2 - r1) * eased_progress)
        g = int(g1 + (g2 - g1) * eased_progress)
        b = int(b1 + (b2 - b1) * eased_progress)
        return (r, g, b)

    def handle_event(self, event):
        was_hovered = self.is_hovered
        
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
            # hover sound when mouse hovers
            if self.is_hovered and not was_hovered and self.hover_sound:
                self.hover_sound.play()
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered:
                if self.click_sound:
                    self.click_sound.play()
                return True
        return False

class CustomCursor:
    def __init__(self):
        self.cursor_size = 20
        self.cursor_color = (0, 0, 0)
        self.cursor_outline = (255, 255, 255)
        self.cursor_surface = pygame.Surface((self.cursor_size, self.cursor_size), pygame.SRCALPHA)
        self.draw_cursor()
        
    def draw_cursor(self):
        self.cursor_surface.fill((0, 0, 0, 0))
        # Draw outer circle
        pygame.draw.circle(self.cursor_surface, self.cursor_outline, 
                         (self.cursor_size//2, self.cursor_size//2), self.cursor_size//2)
        # Draw inner circle
        pygame.draw.circle(self.cursor_surface, self.cursor_color,
                         (self.cursor_size//2, self.cursor_size//2), self.cursor_size//4)
        
    def draw(self, screen, pos):
        screen.blit(self.cursor_surface, (pos[0] - self.cursor_size//2, pos[1] - self.cursor_size//2))

class Settings:
    def __init__(self):
        self.settings_file = "settings.json"
        self.default_settings = {
            "fullscreen": False,
            "music_enabled": True,
            "antialiasing_enabled": True
        }
        self.current_settings = self.load_settings()
        
    def load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    # Ensure all default settings are present
                    for key, value in self.default_settings.items():
                        if key not in loaded_settings:
                            loaded_settings[key] = value
                    return loaded_settings
            except:
                return self.default_settings.copy()
        return self.default_settings.copy()
        
    def save_settings(self):
        with open(self.settings_file, 'w') as f:
            json.dump(self.current_settings, f)
            
    def update_setting(self, key, value):
        self.current_settings[key] = value
        self.save_settings()

class BugReportMenu:
    def __init__(self, screen, color_scheme=None):
        self.screen = screen
        self.settings = Settings()
        self.width = screen.get_width()
        self.height = screen.get_height()
        self.cursor = CustomCursor()
        
        # Use the provided color scheme directly
        self.color_scheme = color_scheme or COLOR_SCHEMES["EASY"]
        
        # Create the bug report form
        form_width = 600
        form_height = 500
        form_x = (self.width - form_width) // 2
        form_y = (self.height - form_height) // 2
        
        self.form_rect = pygame.Rect(form_x, form_y, form_width, form_height)
        
        # Create text box for bug description
        text_box_width = form_width - 40
        text_box_height = 200
        text_box_x = form_x + 20
        text_box_y = form_y + 120
        
        self.text_box = TextBox(text_box_x, text_box_y, text_box_width, text_box_height, 
                               font_size=24, color_scheme=self.color_scheme, max_chars=200)
        
        # Create buttons
        button_width = 200
        button_height = 50
        button_spacing = 40
        
        self.submit_button = Button(
            form_x + button_spacing,
            form_y + form_height - button_height - 20,
            button_width, button_height, "SUBMIT", 32,
            sound_file='assets/settings_menu_click.wav',
            color_scheme=self.color_scheme
        )
        
        self.back_button = Button(
            form_x + form_width - button_width - button_spacing,
            form_y + form_height - button_height - 20,
            button_width, button_height, "BACK", 32,
            sound_file='assets/settings_menu_click.wav',
            color_scheme=self.color_scheme
        )
        
        self.title_font = pygame.font.Font(None, 64)
        
        # System info
        self.system_info = self.get_system_info()
        
        # Success message flag
        self.show_success = False
        self.success_timer = 0
        self.success_duration = 3000  # 3 seconds
        
        # Fade transition
        self.fade_alpha = 0
        self.fade_speed = 5
        self.fade_in = True
        self.fade_out = False
        self.fade_start_time = 0
        self.fade_duration = 5000  # 5 seconds
        
    def get_system_info(self):

        info = {
            "OS": platform.system() + " " + platform.release(),
            "Python": platform.python_version(),
            "Pygame": pygame.version.ver,
            "Screen Resolution": f"{self.width}x{self.height}",
            "Fullscreen": pygame.display.get_surface().get_flags() & pygame.FULLSCREEN != 0
        }
        
        # Get game settings
        try:
            with open("settings.json", 'r') as f:
                settings = json.load(f)
                info["Game Settings"] = settings
        except:
            info["Game Settings"] = "Could not load settings"
            
        return info
        
    def send_to_discord(self, bug_description):

        if DISCORD_WEBHOOK_URL == "YOUR_DISCORD_WEBHOOK_URL_HERE":
            print("Discord webhook URL not configured")
            return False
            
        # Format system info with better organization
        system_info_text = ""
        
        # Add OS and Python info
        system_info_text += "**System Details:**\n"
        system_info_text += f"• OS: {self.system_info['OS']}\n"
        system_info_text += f"• Python: {self.system_info['Python']}\n"
        system_info_text += f"• Pygame: {self.system_info['Pygame']}\n"
        system_info_text += f"• Resolution: {self.system_info['Screen Resolution']}\n"
        system_info_text += f"• Fullscreen: {'Yes' if self.system_info['Fullscreen'] else 'No'}\n\n"
        
        # Add game settings
        system_info_text += "**Game Settings:**\n"
        if isinstance(self.system_info['Game Settings'], dict):
            for key, value in self.system_info['Game Settings'].items():
                # Format boolean values as Yes/No
                if isinstance(value, bool):
                    value = "Yes" if value else "No"
                system_info_text += f"• {key.replace('_', ' ').title()}: {value}\n"
        else:
            system_info_text += "• Settings could not be loaded\n"
                
        # Create the message with improved formatting
        message = {
            "content": "🐛 **New Bug Report Received**",
            "embeds": [
                {
                    "title": "Bug Report Details",
                    "description": f"```\n{bug_description}\n```",
                    "color": 16711680,  # Red color
                    "fields": [
                        {
                            "name": "System Information",
                            "value": system_info_text,
                            "inline": False
                        }
                    ],
                    "footer": {
                        "text": "Ping Pong Modernized Bug Report",
                        "icon_url": "https://cdn.discordapp.com/emojis/1234567890.png"  # Replace with actual icon URL if available
                    },
                    "timestamp": datetime.datetime.utcnow().isoformat()
                }
            ]
        }
        
        try:
            response = requests.post(DISCORD_WEBHOOK_URL, json=message)
            return response.status_code == 204
        except Exception as e:
            print(f"Error sending to Discord: {e}")
            return False
            
    def run(self):
        self.fade_in = True
        self.fade_out = False
        self.fade_alpha = 0
        
        while True:
            self.width = self.screen.get_width()
            self.height = self.screen.get_height()
            
            # Handle fade effects
            if self.fade_in:
                self.fade_alpha = min(255, self.fade_alpha + self.fade_speed)
                if self.fade_alpha >= 255:
                    self.fade_in = False
            elif self.fade_out:
                self.fade_alpha = max(0, self.fade_alpha - self.fade_speed)
                if self.fade_alpha <= 0:
                    return "back"
            
            # Draw background with gradient
            bg_start, bg_end = self.color_scheme["background"]
            self.screen.fill(bg_start)
            gradient_steps = 12
            step_height = self.height / gradient_steps
            
            for i in range(gradient_steps):
                r = int(bg_start[0] + (bg_end[0] - bg_start[0]) * (i / gradient_steps))
                g = int(bg_start[1] + (bg_end[1] - bg_start[1]) * (i / gradient_steps))
                b = int(bg_start[2] + (bg_end[2] - bg_start[2]) * (i / gradient_steps))
                color = (r, g, b)
                pygame.draw.rect(self.screen, color,
                               (0, i * step_height, self.width, step_height + 1))
            
            # Draw title - moved up to prevent overlap
            title = self.title_font.render("REPORT A BUG", True, self.color_scheme["text"])
            title_rect = title.get_rect(centerx=self.width // 2, centery=self.height // 6)  # Changed from height // 5 to height // 6
            
            # Draw title shadow
            for offset in range(4, 0, -1):
                shadow_rect = title_rect.copy()
                shadow_rect.x += offset
                shadow_rect.y += offset
                shadow = self.title_font.render("REPORT A BUG", True, 
                                              (220 - offset*10, 220 - offset*10, 220 - offset*10))
                self.screen.blit(shadow, shadow_rect)
            
            self.screen.blit(title, title_rect)
            
            # Draw description text
            desc_font = pygame.font.Font(None, 28)
            desc_text = "Please describe the bug you encountered :3"
            desc_surface = desc_font.render(desc_text, True, self.color_scheme["text"])
            desc_rect = desc_surface.get_rect(centerx=self.width // 2, y=self.text_box.rect.y - 30)
            self.screen.blit(desc_surface, desc_rect)
            
            # Draw text box
            self.text_box.draw(self.screen)
            
            # Draw buttons
            self.submit_button.draw(self.screen)
            self.back_button.draw(self.screen)
            
            # Draw success message if active
            if self.show_success:
                success_font = pygame.font.Font(None, 24)  # Smaller font
                success_text = "Bug report sent successfully!"
                success_surface = success_font.render(success_text, True, (0, 200, 0))
                success_rect = success_surface.get_rect(centerx=self.width // 2, 
                                                      bottom=self.height - 40)  # Above the privacy note
                self.screen.blit(success_surface, success_rect)
            
            # Draw privacy note
            privacy_font = pygame.font.Font(None, 20)
            privacy_text = "Note: Only system information such as OS, Game settings, Python, Pygame version and game logs are shared."
            privacy_surface = privacy_font.render(privacy_text, True, (100, 100, 100))
            privacy_rect = privacy_surface.get_rect(centerx=self.width // 2, 
                                                  bottom=self.height - 20)
            self.screen.blit(privacy_surface, privacy_rect)
            
            # Draw cursor
            mouse_pos = pygame.mouse.get_pos()
            self.cursor.draw(self.screen, mouse_pos)
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                    
                if self.text_box.handle_event(event):
                    pass
                    
                if self.submit_button.handle_event(event):
                    bug_description = self.text_box.get_text()
                    if bug_description:
                        if self.send_to_discord(bug_description):
                            # Show success message
                            self.show_success = True
                            self.success_timer = pygame.time.get_ticks()
                            
                            # Start fade out after success message duration
                            self.fade_start_time = pygame.time.get_ticks()
                            self.fade_out = True
                            
                        return "back"
                        
                if self.back_button.handle_event(event):
                    # Start fade out
                    self.fade_out = True
            
            # Update success message timer
            if self.show_success:
                if pygame.time.get_ticks() - self.success_timer > self.success_duration:
                    self.show_success = False
                    
            pygame.display.flip()

class Menu:
    def __init__(self, screen):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # initialize settings and cursor
        self.settings = Settings()
        self.cursor = CustomCursor()
        
        # initial fullscreen state
        if self.settings.current_settings['fullscreen']:
            pygame.display.toggle_fullscreen()
            # Update screen dimensions after fullscreen toggle
            self.width = screen.get_width()
            self.height = screen.get_height()
        
        # make cursor visible in menu
        pygame.mouse.set_visible(False)
        
        button_width = 240
        button_height = 60
        vertical_spacing = 80
        
        start_y = self.height // 2 + 40
        
        self.difficulty = "EASY"
        
        button_x = self.width // 2 - button_width // 2
        
        self.play_button = Button(button_x, start_y - vertical_spacing * 2,
                                button_width, button_height, "PLAY", 42, 
                                sound_file='assets/play_click.wav',
                                color_scheme=COLOR_SCHEMES["EASY"])
        self.difficulty_button = Button(button_x, start_y - vertical_spacing,
                                      button_width, button_height, f"AI: {self.difficulty}", 42,
                                      sound_file='assets/settings_menu_click.wav',
                                      color_scheme=COLOR_SCHEMES["EASY"])
        self.settings_button = Button(button_x, start_y,
                                    button_width, button_height, "SETTINGS", 42,
                                    sound_file='assets/settings_click.wav',
                                    color_scheme=COLOR_SCHEMES["EASY"])
        self.quit_button = Button(button_x, start_y + vertical_spacing,
                                button_width, button_height, "QUIT", 42,
                                sound_file='assets/settings_menu_click.wav',
                                color_scheme=COLOR_SCHEMES["EASY"])
        
        # Add bug report button (question mark icon)
        bug_button_size = 50
        bug_button_x = self.width - bug_button_size - 20
        bug_button_y = self.height - bug_button_size - 20
        
        self.bug_report_button = Button(bug_button_x, bug_button_y, 
                                       bug_button_size, bug_button_size, "", 
                                       font_size=36, 
                                       sound_file='assets/settings_menu_click.wav',
                                       color_scheme=COLOR_SCHEMES["EASY"],
                                       icon="?")
        
        # Add info button (i icon)
        info_button_size = 50
        info_button_x = 20
        info_button_y = self.height - info_button_size - 20
        
        self.info_button = Button(info_button_x, info_button_y, 
                                 info_button_size, info_button_size, "", 
                                 font_size=36, 
                                 sound_file='assets/settings_menu_click.wav',
                                 color_scheme=COLOR_SCHEMES["EASY"],
                                 icon="i")
        
        # Add trophy button (trophy icon)
        trophy_button_size = 50
        trophy_button_x = info_button_x + trophy_button_size + 10
        trophy_button_y = info_button_y
        
        self.trophy_button = Button(trophy_button_x, trophy_button_y, 
                                   trophy_button_size, trophy_button_size, "", 
                                   font_size=36, 
                                   sound_file='assets/settings_menu_click.wav',
                                   color_scheme=COLOR_SCHEMES["EASY"],
                                   icon="🏆")
        
        self.title_font = pygame.font.Font(None, 96)
        
        self.color_transition_progress = 0
        self.current_color_scheme = COLOR_SCHEMES["EASY"]
        self.target_color_scheme = COLOR_SCHEMES["EASY"]
        
    def update_color_transition(self, speed=0.01):

        if self.color_transition_progress < 1.0:
            self.color_transition_progress = min(1.0, self.color_transition_progress + speed)
            return True
        return False
        
    def interpolate_color(self, color1, color2, progress):

        eased_progress = progress * progress * (3 - 2 * progress)
        
        r1, g1, b1 = color1
        r2, g2, b2 = color2
        r = int(r1 + (r2 - r1) * eased_progress)
        g = int(g1 + (g2 - g1) * eased_progress)
        b = int(b1 + (b2 - b1) * eased_progress)
        return (r, g, b)
        
    def run_settings_menu(self):
        # Pass the target color scheme instead of current
        settings_menu = SettingsMenu(self.screen, self.settings, self.target_color_scheme)
        return settings_menu.run()
        
    def run_bug_report_menu(self):
        # Pass the target color scheme instead of current
        bug_report_menu = BugReportMenu(self.screen, self.target_color_scheme)
        return bug_report_menu.run()
        
    def run_info_menu(self):
        # Pass the target color scheme instead of current
        info_menu = InfoMenu(self.screen, self.target_color_scheme)
        return info_menu.run()
        
    def run_global_scores_menu(self, score=None):
        # Pass the target color scheme instead of current
        global_scores_menu = GlobalScoresMenu(self.screen, self.target_color_scheme, score)
        return global_scores_menu.run()
        
    def run(self):
        while True:
            self.width = self.screen.get_width()
            self.height = self.screen.get_height()
            
            self.update_color_transition()
            
            bg_start = self.interpolate_color(
                self.current_color_scheme["background"][0],
                self.target_color_scheme["background"][0],
                self.color_transition_progress
            )
            bg_end = self.interpolate_color(
                self.current_color_scheme["background"][1],
                self.target_color_scheme["background"][1],
                self.color_transition_progress
            )
            
            self.screen.fill(bg_start)
            gradient_steps = 12
            step_height = self.height / gradient_steps
            
            for i in range(gradient_steps):
                r = int(bg_start[0] + (bg_end[0] - bg_start[0]) * (i / gradient_steps))
                g = int(bg_start[1] + (bg_end[1] - bg_start[1]) * (i / gradient_steps))
                b = int(bg_start[2] + (bg_end[2] - bg_start[2]) * (i / gradient_steps))
                color = (r, g, b)
                pygame.draw.rect(self.screen, color,
                               (0, i * step_height, self.width, step_height + 1))
            
            title_shadow = self.title_font.render("mit's ping bang", True, (200, 200, 200))
            title = self.title_font.render("• PING BANG •", True, (0, 0, 0))
            
            title_rect = title.get_rect(centerx=self.width // 2, centery=self.height // 5)
            
            for offset in range(4, 0, -1):
                shadow_rect = title_rect.copy()
                shadow_rect.x += offset
                shadow_rect.y += offset
                shadow = self.title_font.render("• PING BANG •", True, 
                                              (220 - offset*10, 220 - offset*10, 220 - offset*10))
                self.screen.blit(shadow, shadow_rect)
            
            self.screen.blit(title, title_rect)
            
            button_width = 240
            button_height = 60
            vertical_spacing = 80
            start_y = self.height // 2 + 40
            button_x = self.width // 2 - button_width // 2
            
            self.play_button.original_rect.x = button_x
            self.play_button.original_rect.y = start_y - vertical_spacing * 2
            self.play_button.rect.x = button_x
            self.play_button.rect.y = start_y - vertical_spacing * 2
            
            self.difficulty_button.original_rect.x = button_x
            self.difficulty_button.original_rect.y = start_y - vertical_spacing
            self.difficulty_button.rect.x = button_x
            self.difficulty_button.rect.y = start_y - vertical_spacing
            
            self.settings_button.original_rect.x = button_x
            self.settings_button.original_rect.y = start_y
            self.settings_button.rect.x = button_x
            self.settings_button.rect.y = start_y
            
            self.quit_button.original_rect.x = button_x
            self.quit_button.original_rect.y = start_y + vertical_spacing
            self.quit_button.rect.x = button_x
            self.quit_button.rect.y = start_y + vertical_spacing
            
            # Update bug report button position
            bug_button_size = 50
            bug_button_x = self.width - bug_button_size - 20
            bug_button_y = self.height - bug_button_size - 20
            
            self.bug_report_button.original_rect.x = bug_button_x
            self.bug_report_button.original_rect.y = bug_button_y
            self.bug_report_button.rect.x = bug_button_x
            self.bug_report_button.rect.y = bug_button_y
            
            # Update info button position
            info_button_size = 50
            info_button_x = 20
            info_button_y = self.height - info_button_size - 20
            
            self.info_button.original_rect.x = info_button_x
            self.info_button.original_rect.y = info_button_y
            self.info_button.rect.x = info_button_x
            self.info_button.rect.y = info_button_y
            
            # Update trophy button position
            trophy_button_size = 50
            trophy_button_x = info_button_x + trophy_button_size + 10
            trophy_button_y = info_button_y
            
            self.trophy_button.original_rect.x = trophy_button_x
            self.trophy_button.original_rect.y = trophy_button_y
            self.trophy_button.rect.x = trophy_button_x
            self.trophy_button.rect.y = trophy_button_y
            
            self.play_button.draw(self.screen)
            self.difficulty_button.draw(self.screen)
            self.settings_button.draw(self.screen)
            self.quit_button.draw(self.screen)
            self.bug_report_button.draw(self.screen)
            self.info_button.draw(self.screen)
            self.trophy_button.draw(self.screen)
            
            mouse_pos = pygame.mouse.get_pos()
            self.cursor.draw(self.screen, mouse_pos)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                    
                if self.play_button.handle_event(event):
                    return f"game:{self.difficulty.lower()}"
                if self.difficulty_button.handle_event(event):
                    if self.difficulty == "EASY":
                        self.difficulty = "MEDIUM"
                        # Change background music for medium difficulty
                        try:
                            pygame.mixer.music.load('assets/medium_music.wav')
                            pygame.mixer.music.play(-1)
                            if self.settings.current_settings['music_enabled']:
                                pygame.mixer.music.set_volume(1.0)  # Set music volume to 1.0
                            else:
                                pygame.mixer.music.set_volume(0.0)
                        except:
                            print("Medium difficulty music file not found")
                    elif self.difficulty == "MEDIUM":
                        self.difficulty = "HARD"
                        # Change background music for hard difficulty
                        try:
                            pygame.mixer.music.load('assets/hard_music.wav')
                            pygame.mixer.music.play(-1)
                            if self.settings.current_settings['music_enabled']:
                                pygame.mixer.music.set_volume(1.0)  # Set music volume to 1.0
                            else:
                                pygame.mixer.music.set_volume(0.0)
                        except:
                            print("Hard difficulty music file not found")
                    else:
                        self.difficulty = "EASY"
                        # Change back to normal background music for easy difficulty
                        try:
                            pygame.mixer.music.load('assets/background_music.wav')
                            pygame.mixer.music.play(-1)
                            if self.settings.current_settings['music_enabled']:
                                pygame.mixer.music.set_volume(1.0)  # Set music volume to 1.0
                            else:
                                pygame.mixer.music.set_volume(0.0)
                        except:
                            print("Easy difficulty music file not found")
                    self.difficulty_button.text = f"AI: {self.difficulty}"
                    
                    # Update color scheme for all buttons
                    self.target_color_scheme = COLOR_SCHEMES[self.difficulty]
                    self.color_transition_progress = 0  # Reset transition progress
                    
                    # Update button color schemes
                    self.play_button.set_color_scheme(COLOR_SCHEMES[self.difficulty])
                    self.difficulty_button.set_color_scheme(COLOR_SCHEMES[self.difficulty])
                    self.settings_button.set_color_scheme(COLOR_SCHEMES[self.difficulty])
                    self.quit_button.set_color_scheme(COLOR_SCHEMES[self.difficulty])
                    self.bug_report_button.set_color_scheme(COLOR_SCHEMES[self.difficulty])
                    self.info_button.set_color_scheme(COLOR_SCHEMES[self.difficulty])
                    self.trophy_button.set_color_scheme(COLOR_SCHEMES[self.difficulty])
                    
                if self.settings_button.handle_event(event):
                    result = self.run_settings_menu()
                    if result == "fullscreen_toggle":
                        # Handle fullscreen toggle
                        pygame.display.toggle_fullscreen()
                        # Update screen dimensions after fullscreen toggle
                        self.width = self.screen.get_width()
                        self.height = self.screen.get_height()
                    elif result == "back":
                        continue
                        
                if self.bug_report_button.handle_event(event):
                    result = self.run_bug_report_menu()
                    if result == "back":
                        continue
                    
                if self.info_button.handle_event(event):
                    result = self.run_info_menu()
                    if result == "back":
                        continue
                    
                if self.trophy_button.handle_event(event):
                    result = self.run_global_scores_menu()
                    if result == "back":
                        continue
                    
                if self.quit_button.handle_event(event):
                    return "quit"
                    
            pygame.display.flip()

class SettingsMenu:
    def __init__(self, screen, settings, color_scheme=None):
        self.screen = screen
        self.settings = settings
        self.width = screen.get_width()
        self.height = screen.get_height()
        self.cursor = CustomCursor()
        
        # Use the provided color scheme directly
        self.color_scheme = color_scheme or COLOR_SCHEMES["EASY"]
        
        button_width = 300
        button_height = 60
        vertical_spacing = 80
        start_y = self.height // 2 + 40
        button_x = self.width // 2 - button_width // 2
        
        self.fullscreen_button = Button(button_x, start_y - vertical_spacing * 2,
                                      button_width, button_height,
                                      f"FULLSCREEN: {'ON' if self.settings.current_settings['fullscreen'] else 'OFF'}", 42,
                                      sound_file='assets/settings_menu_click.wav',
                                      color_scheme=self.color_scheme)
        
        self.music_button = Button(button_x, start_y - vertical_spacing,
                                 button_width, button_height,
                                 f"MUSIC: {'ON' if self.settings.current_settings['music_enabled'] else 'OFF'}", 42,
                                 sound_file='assets/settings_menu_click.wav',
                                 color_scheme=self.color_scheme)
        
        self.antialiasing_button = Button(button_x, start_y,
                                        button_width, button_height,
                                        f"ANTIALIASING: {'ON' if self.settings.current_settings['antialiasing_enabled'] else 'OFF'}", 42,
                                        sound_file='assets/settings_menu_click.wav',
                                        color_scheme=self.color_scheme)
        
        self.back_button = Button(button_x, start_y + vertical_spacing * 2,
                                button_width, button_height, "BACK", 42,
                                sound_file='assets/settings_menu_click.wav',
                                color_scheme=self.color_scheme)
        
        self.title_font = pygame.font.Font(None, 96)
        
    def run(self):
        while True:
            self.width = self.screen.get_width()
            self.height = self.screen.get_height()
            
            bg_start, bg_end = self.color_scheme["background"]
            self.screen.fill(bg_start)
            gradient_steps = 12
            step_height = self.height / gradient_steps
            
            for i in range(gradient_steps):
                r = int(bg_start[0] + (bg_end[0] - bg_start[0]) * (i / gradient_steps))
                g = int(bg_start[1] + (bg_end[1] - bg_start[1]) * (i / gradient_steps))
                b = int(bg_start[2] + (bg_end[2] - bg_start[2]) * (i / gradient_steps))
                color = (r, g, b)
                pygame.draw.rect(self.screen, color,
                               (0, i * step_height, self.width, step_height + 1))
            
            title = self.title_font.render("SETTINGS", True, self.color_scheme["text"])
            
            title_rect = title.get_rect(centerx=self.width // 2, centery=self.height // 5)
            
            for offset in range(4, 0, -1):
                shadow_rect = title_rect.copy()
                shadow_rect.x += offset
                shadow_rect.y += offset
                shadow = self.title_font.render("SETTINGS", True, 
                                              (220 - offset*10, 220 - offset*10, 220 - offset*10))
                self.screen.blit(shadow, shadow_rect)
            
            self.screen.blit(title, title_rect)
            
            button_width = 300
            button_height = 60
            vertical_spacing = 80
            start_y = self.height // 2 + 40
            button_x = self.width // 2 - button_width // 2
            
            self.fullscreen_button.original_rect.x = button_x
            self.fullscreen_button.original_rect.y = start_y - vertical_spacing * 2
            self.fullscreen_button.rect.x = button_x
            self.fullscreen_button.rect.y = start_y - vertical_spacing * 2
            
            self.music_button.original_rect.x = button_x
            self.music_button.original_rect.y = start_y - vertical_spacing
            self.music_button.rect.x = button_x
            self.music_button.rect.y = start_y - vertical_spacing
            
            self.antialiasing_button.original_rect.x = button_x
            self.antialiasing_button.original_rect.y = start_y
            self.antialiasing_button.rect.x = button_x
            self.antialiasing_button.rect.y = start_y
            
            self.back_button.original_rect.x = button_x
            self.back_button.original_rect.y = start_y + vertical_spacing * 2
            self.back_button.rect.x = button_x
            self.back_button.rect.y = start_y + vertical_spacing * 2
            
            self.fullscreen_button.draw(self.screen)
            self.music_button.draw(self.screen)
            self.antialiasing_button.draw(self.screen)
            self.back_button.draw(self.screen)
            
            mouse_pos = pygame.mouse.get_pos()
            self.cursor.draw(self.screen, mouse_pos)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                    
                if self.fullscreen_button.handle_event(event):
                    current_state = self.settings.current_settings['fullscreen']
                    self.settings.update_setting('fullscreen', not current_state)
                    self.fullscreen_button.text = f"FULLSCREEN: {'ON' if not current_state else 'OFF'}"
                    return "fullscreen_toggle"
                
                if self.music_button.handle_event(event):
                    current_state = self.settings.current_settings['music_enabled']
                    self.settings.update_setting('music_enabled', not current_state)
                    self.music_button.text = f"MUSIC: {'ON' if not current_state else 'OFF'}"
                    if not current_state:
                        pygame.mixer.music.set_volume(1.0)
                    else:
                        pygame.mixer.music.set_volume(0.0)
                
                if self.antialiasing_button.handle_event(event):
                    current_state = self.settings.current_settings['antialiasing_enabled']
                    self.settings.update_setting('antialiasing_enabled', not current_state)
                    self.antialiasing_button.text = f"ANTIALIASING: {'ON' if not current_state else 'OFF'}"
                    
                if self.back_button.handle_event(event):
                    return "back"
                    
            pygame.display.flip() 

class InfoMenu:
    def __init__(self, screen, color_scheme=None):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        self.cursor = CustomCursor()
        
        # Use the provided color scheme directly
        self.color_scheme = color_scheme or COLOR_SCHEMES["EASY"]
        
        # Create the info box
        box_width = 500
        box_height = 300
        box_x = (self.width - box_width) // 2
        box_y = (self.height - box_height) // 2
        
        self.box_rect = pygame.Rect(box_x, box_y, box_width, box_height)
        
        # Create buttons with smaller size
        button_width = 150
        button_height = 40
        button_spacing = 20
        
        self.github_button = Button(
            box_x + box_width // 2 - button_width - button_spacing // 2,
            box_y + box_height - button_height - 20,
            button_width, button_height, "GITHUB", 28,
            sound_file='assets/settings_menu_click.wav',
            color_scheme=self.color_scheme
        )
        
        self.source_button = Button(
            box_x + box_width // 2 + button_spacing // 2,
            box_y + box_height - button_height - 20,
            button_width, button_height, "SOURCE", 28,
            sound_file='assets/settings_menu_click.wav',
            color_scheme=self.color_scheme
        )
        
        self.back_button = Button(
            box_x + (box_width - button_width) // 2,
            box_y + box_height + 20,
            button_width, button_height, "BACK", 32,
            sound_file='assets/settings_menu_click.wav',
            color_scheme=self.color_scheme
        )
        
        self.title_font = pygame.font.Font(None, 64)
        self.text_font = pygame.font.Font(None, 32)
        
        # Add text wrapping properties
        self.description_text = "a little fun ping pong game made in a few hours for fun, this game is open source so feel free to make your own version of it!"
        self.text_margin = 40  # Margin from box edges
        self.line_spacing = 5  # Space between wrapped lines
        
    def wrap_text(self, text, font, max_width):

        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            # Test if adding this word would exceed the width
            test_line = ' '.join(current_line + [word])
            text_surface = font.render(test_line, True, self.color_scheme["text"])
            
            if text_surface.get_width() <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                
        if current_line:
            lines.append(' '.join(current_line))
            
        return lines
        
    def run(self):
        while True:
            self.width = self.screen.get_width()
            self.height = self.screen.get_height()
            
            # Draw background with gradient
            bg_start, bg_end = self.color_scheme["background"]
            self.screen.fill(bg_start)
            gradient_steps = 12
            step_height = self.height / gradient_steps
            
            for i in range(gradient_steps):
                r = int(bg_start[0] + (bg_end[0] - bg_start[0]) * (i / gradient_steps))
                g = int(bg_start[1] + (bg_end[1] - bg_start[1]) * (i / gradient_steps))
                b = int(bg_start[2] + (bg_end[2] - bg_start[2]) * (i / gradient_steps))
                color = (r, g, b)
                pygame.draw.rect(self.screen, color,
                               (0, i * step_height, self.width, step_height + 1))
            
            # Draw info box with shadow
            shadow_offset = 10
            shadow_rect = self.box_rect.copy()
            shadow_rect.x += shadow_offset
            shadow_rect.y += shadow_offset
            pygame.draw.rect(self.screen, (50, 50, 50), shadow_rect, border_radius=15)
            
            # Draw info box with a lighter background for better contrast
            box_bg_color = (240, 240, 240) if self.color_scheme == COLOR_SCHEMES["HARD"] else (255, 255, 255)
            pygame.draw.rect(self.screen, box_bg_color, self.box_rect, border_radius=15)
            pygame.draw.rect(self.screen, self.color_scheme["button_border"], self.box_rect, border_radius=15, width=2)
            
            # Draw title with adjusted color for hard mode
            title_color = (180, 30, 50) if self.color_scheme == COLOR_SCHEMES["HARD"] else self.color_scheme["text"]
            title = self.title_font.render("Ping Bang!", True, title_color)
            title_rect = title.get_rect(centerx=self.width // 2, centery=self.box_rect.y + 50)
            
            # Draw title shadow with adjusted color for hard mode
            shadow_color = (100, 0, 20) if self.color_scheme == COLOR_SCHEMES["HARD"] else (220, 220, 220)
            for offset in range(4, 0, -1):
                shadow_rect = title_rect.copy()
                shadow_rect.x += offset
                shadow_rect.y += offset
                shadow = self.title_font.render("Ping Bang!", True, shadow_color)
                self.screen.blit(shadow, shadow_rect)
            
            self.screen.blit(title, title_rect)
            
            # Calculate available width for text
            available_width = self.box_rect.width - (2 * self.text_margin)
            
            # Wrap the description text
            wrapped_lines = self.wrap_text(self.description_text, self.text_font, available_width)
            
            # Draw each line of wrapped text with adjusted color for hard mode
            line_height = self.text_font.get_height() + self.line_spacing
            total_text_height = len(wrapped_lines) * line_height
            start_y = self.box_rect.y + 100
            
            text_color = (40, 40, 40) if self.color_scheme == COLOR_SCHEMES["HARD"] else self.color_scheme["text"]
            for i, line in enumerate(wrapped_lines):
                text_surface = self.text_font.render(line, True, text_color)
                text_rect = text_surface.get_rect(
                    centerx=self.width // 2,
                    y=start_y + (i * line_height)
                )
                self.screen.blit(text_surface, text_rect)
            
            # Draw buttons
            self.github_button.draw(self.screen)
            self.source_button.draw(self.screen)
            self.back_button.draw(self.screen)
            
            # Draw cursor
            mouse_pos = pygame.mouse.get_pos()
            self.cursor.draw(self.screen, mouse_pos)
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                    
                if self.github_button.handle_event(event):
                    # Open GitHub link
                    import webbrowser
                    webbrowser.open("https://github.com/TheDerpyMit")
                    return "back"
                    
                if self.source_button.handle_event(event):
                    # Open source code link
                    import webbrowser
                    webbrowser.open("https://github.com/TheDerpyMit/ping-bang")
                    return "back"
                    
                if self.back_button.handle_event(event):
                    return "back"
                    
            pygame.display.flip() 

class GlobalScoresMenu:
    def __init__(self, screen, color_scheme=None, score_to_submit=None):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        self.cursor = CustomCursor()
        
        # Use the provided color scheme directly
        self.color_scheme = color_scheme or COLOR_SCHEMES["EASY"]
        
        # Create the main box
        box_width = 800
        box_height = 300
        box_x = (self.width - box_width) // 2
        box_y = (self.height - box_height) // 2
        
        self.box_rect = pygame.Rect(box_x, box_y, box_width, box_height)
        
        # Create back button
        button_width = 150
        button_height = 40
        
        self.back_button = Button(
            box_x + (box_width - button_width) // 2,
            box_y + box_height - button_height - 20,
            button_width, button_height, "BACK", 28,
            sound_file='assets/settings_menu_click.wav',
            color_scheme=self.color_scheme
        )
        
        self.title_font = pygame.font.Font(None, 64)
        self.text_font = pygame.font.Font(None, 32)
        
    def run(self):
        while True:
            self.width = self.screen.get_width()
            self.height = self.screen.get_height()
            
            # Draw background with gradient
            bg_start, bg_end = self.color_scheme["background"]
            self.screen.fill(bg_start)
            gradient_steps = 12
            step_height = self.height / gradient_steps
            
            for i in range(gradient_steps):
                r = int(bg_start[0] + (bg_end[0] - bg_start[0]) * (i / gradient_steps))
                g = int(bg_start[1] + (bg_end[1] - bg_start[1]) * (i / gradient_steps))
                b = int(bg_start[2] + (bg_end[2] - bg_start[2]) * (i / gradient_steps))
                color = (r, g, b)
                pygame.draw.rect(self.screen, color,
                               (0, i * step_height, self.width, step_height + 1))
            
            # Draw main box
            box_bg_color = (240, 240, 240) if self.color_scheme == COLOR_SCHEMES["HARD"] else (255, 255, 255)
            pygame.draw.rect(self.screen, box_bg_color, self.box_rect, border_radius=15)
            pygame.draw.rect(self.screen, self.color_scheme["button_border"], self.box_rect, border_radius=15, width=2)
            
            # Draw title
            title = self.title_font.render("Global Leaderboard", True, self.color_scheme["text"])
            title_rect = title.get_rect(centerx=self.width // 2, y=self.box_rect.y + 40)
            self.screen.blit(title, title_rect)
            
            # Draw coming soon message
            coming_soon = self.text_font.render("Feature coming soon...", True, self.color_scheme["text"])
            coming_soon_rect = coming_soon.get_rect(centerx=self.width // 2, centery=self.box_rect.centery)
            self.screen.blit(coming_soon, coming_soon_rect)
            
            # Draw back button
            self.back_button.draw(self.screen)
            
            # Draw cursor
            mouse_pos = pygame.mouse.get_pos()
            self.cursor.draw(self.screen, mouse_pos)
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                    
                if self.back_button.handle_event(event):
                    return "back"
                    
            pygame.display.flip() 