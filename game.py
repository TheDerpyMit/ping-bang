import pygame
import random
from pygame import gfxdraw
from menu import Button

class Paddle:
    def __init__(self, x, y, width, height, is_ai=False, ai_difficulty="medium"):
        self.rect = pygame.Rect(x, y, width, height)
        self.speed = 5
        self.score = 0
        self.alive = True
        self.is_ai = is_ai
        self.ai_difficulty = ai_difficulty
        self.target_y = y
        self.position_y = float(y)
        self.prediction_offset = 0
        self.velocity = 0  
        self.smoothing = 0.92  
        self.screen_height = pygame.display.get_surface().get_height()
        
    def move(self, up=True):
        if up and self.rect.top > 0:
            self.rect.y -= self.speed
        if not up and self.rect.bottom < self.screen_height:
            self.rect.y += self.speed
    
    def move_to_mouse(self, target_y):
        self.target_y = target_y - self.rect.height / 2
        self.target_y = max(0, min(self.target_y, self.screen_height - self.rect.height))
        diff = self.target_y - self.rect.y
        if abs(diff) > self.speed:
            self.rect.y += self.speed * (1 if diff > 0 else -1)
        else:
            self.rect.y = self.target_y

    def ai_move(self, ball, extra_ball=None):
        if not self.is_ai or not self.alive:
            return
            
        
        self.screen_height = pygame.display.get_surface().get_height()
            
        
        if self.ai_difficulty == "easy":
            reaction_speed = 0.008  
            prediction_noise = 100  
            max_speed = 2.5
            self.smoothing = 0.985  
            prediction_smoothing = 0.03  
            acceleration_factor = 0.3  
        elif self.ai_difficulty == "medium":
            reaction_speed = 0.025  
            prediction_noise = 50  
            max_speed = 3.5
            self.smoothing = 0.95  
            prediction_smoothing = 0.08  
            acceleration_factor = 0.5  
        else:  
            reaction_speed = 0.04  
            prediction_noise = 25  
            max_speed = 4.5
            self.smoothing = 0.92  
            prediction_smoothing = 0.12  
            acceleration_factor = 0.7  
            
        
        target_offset = random.uniform(-prediction_noise, prediction_noise)
        self.prediction_offset += (target_offset - self.prediction_offset) * prediction_smoothing
        
        
        target_ball = ball
        if extra_ball:
            
            main_ball_moving_toward = ball.speed_x > 0  
            extra_ball_moving_toward = extra_ball.speed_x > 0  
            
            if main_ball_moving_toward and extra_ball_moving_toward:
                
                dist_to_main = abs(self.rect.centerx - ball.rect.centerx)
                dist_to_extra = abs(self.rect.centerx - extra_ball.rect.centerx)
                if dist_to_extra < dist_to_main:
                    target_ball = extra_ball
            elif extra_ball_moving_toward and not main_ball_moving_toward:
                
                target_ball = extra_ball
            elif not main_ball_moving_toward and not extra_ball_moving_toward:
                
                dist_to_main = abs(self.rect.centerx - ball.rect.centerx)
                dist_to_extra = abs(self.rect.centerx - extra_ball.rect.centerx)
                if dist_to_extra < dist_to_main:
                    target_ball = extra_ball
        
        
        if self.ai_difficulty == "hard":
            
            
            if target_ball.speed_x != 0:  
                time_to_paddle = (self.rect.centerx - target_ball.rect.centerx) / target_ball.speed_x
                if time_to_paddle > 0:  
                    
                    predicted_y = target_ball.rect.centery + (target_ball.speed_y * time_to_paddle)
                    
                    predicted_y += random.uniform(-prediction_noise, prediction_noise)
                    self.target_y = predicted_y
                else:
                    
                    self.target_y = target_ball.rect.centery + self.prediction_offset
            else:
                self.target_y = target_ball.rect.centery + self.prediction_offset
        else:
            
            self.target_y = target_ball.rect.centery + self.prediction_offset
        
        
        self.target_y = max(self.rect.height/2, min(self.target_y, self.screen_height - self.rect.height/2))
        
        
        diff = self.target_y - (self.position_y + self.rect.height/2)
        
        
        
        if abs(diff) > 0.1:  
            
            distance_factor = min(1.0, abs(diff) / 100)
            
            
            desired_velocity = diff * reaction_speed * (0.3 + 0.7 * distance_factor) * acceleration_factor
            
            
            self.velocity = (self.velocity * self.smoothing + 
                           desired_velocity * (1 - self.smoothing))
            
            
            self.velocity = max(min(self.velocity, max_speed), -max_speed)
            
            
            self.position_y += self.velocity
            
            
            self.position_y = max(0, min(self.position_y, self.screen_height - self.rect.height))
        
        
        self.rect.y = round(self.position_y)
            
    def draw(self, screen, antialiasing_enabled=True):
        color = (255, 255, 255) if self.alive else (100, 100, 100)
        
        if antialiasing_enabled:
            
            
            pygame.draw.rect(screen, color, self.rect, border_radius=8)
            
            
            radius = 8
            for i in range(radius):
                alpha = int(255 * (1 - i/radius))
                edge_color = (*color, alpha)
                
                
                edge_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
                
                
                pygame.draw.rect(edge_surface, edge_color, 
                               (0, 0, self.rect.width, self.rect.height), 
                               border_radius=radius-i)
                
                
                screen.blit(edge_surface, self.rect)
        else:
            
            pygame.draw.rect(screen, color, self.rect)

class Ball:
    def __init__(self, x, y, size, max_speed=None, difficulty="medium"):
        self.rect = pygame.Rect(x, y, size, size)
        
        if difficulty == "easy":
            self.base_speed = 0.1
        elif difficulty == "medium":
            self.base_speed = 0.5
        else:  
            self.base_speed = 1.5
        self.speed_increment = 0.1
        self.current_speed = self.base_speed
        self.position_x = float(x)
        self.position_y = float(y)
        self.left_hit_count = 0  
        self.right_hit_count = 0  
        self.max_speed = max_speed  
        self.difficulty = difficulty  
        self.color = (255, 255, 255)  
        self.reset_ball()
        self.size = size
        self.last_collision_time = 0  
        
    def reset_ball(self):
        self.current_speed = self.base_speed
        self.position_x = float(self.rect.x)
        self.position_y = float(self.rect.y)
        self.left_hit_count = 0  
        self.right_hit_count = 0  
        direction_x = random.choice((1, -1))
        
        direction_y = random.uniform(-0.2, 0.2)
        self.speed_x = self.current_speed * direction_x
        self.speed_y = self.current_speed * direction_y
        
    def move(self):
        
        self.position_x += self.speed_x
        self.position_y += self.speed_y
        
        
        self.rect.x = round(self.position_x)
        self.rect.y = round(self.position_y)
        
    def draw(self, screen, antialiasing_enabled=True):
        if antialiasing_enabled:
            
            radius = self.size // 2
            
            
            circle_surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            
            
            pygame.draw.circle(circle_surface, (*self.color, 255), 
                             (radius, radius), radius)
            
            
            for i in range(3):
                edge_radius = radius - i
                alpha = int(255 * (1 - i/3))
                pygame.draw.circle(circle_surface, (*self.color, alpha), 
                                 (radius, radius), edge_radius)
            
            
            screen.blit(circle_surface, self.rect)
        else:
            
            pygame.draw.circle(screen, self.color, 
                             (self.rect.centerx, self.rect.centery), self.size // 2)
        
    def bounce(self):
        self.speed_y *= -1
        
    def bounce_paddle(self, is_left_paddle=True):
        
        current_time = pygame.time.get_ticks()
        if current_time - self.last_collision_time < 100:  
            return
            
        self.last_collision_time = current_time
        
        self.speed_x *= -1
        
        if is_left_paddle:
            self.left_hit_count += 1
            if self.left_hit_count % 2 == 0:
                self.current_speed += self.speed_increment
        else:
            self.right_hit_count += 1
            if self.right_hit_count % 2 == 0:
                self.current_speed += self.speed_increment
            
            
        if self.max_speed is not None and self.current_speed > self.max_speed:
            self.current_speed = self.max_speed
            
        
        total_speed = (self.speed_x ** 2 + self.speed_y ** 2) ** 0.5
        if total_speed > 0:  
            self.speed_x = (self.speed_x / total_speed) * self.current_speed
            self.speed_y = (self.speed_y / total_speed) * self.current_speed
            
        
        if self.speed_x > 0:
            self.position_x = self.rect.right + 5
        else:
            self.position_x = self.rect.left - 5

class GameModifier:
    def __init__(self, x, y, modifier_type):
        self.rect = pygame.Rect(x, y, 30, 30)  
        self.type = modifier_type
        self.active = True
        self.color = self.get_color()
        
    def get_color(self):
        if self.type == "paddle_size":
            return (255, 0, 0)  
        elif self.type == "ball_speed":
            return (0, 255, 0)  
        elif self.type == "extra_ball":
            return (255, 255, 0)  
        return (255, 255, 255)
        
    def draw(self, screen, antialiasing_enabled=True):
        if antialiasing_enabled:
            
            circle_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            pygame.draw.circle(circle_surface, (*self.color, 255), 
                             (self.rect.width//2, self.rect.height//2), self.rect.width//2)
            screen.blit(circle_surface, self.rect)
        else:
            pygame.draw.circle(screen, self.color, 
                             (self.rect.centerx, self.rect.centery), self.rect.width//2)

class Game:
    def __init__(self, screen, ai_difficulty="medium"):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        
        if ai_difficulty == "easy":
            self.max_ball_speed = 2.5
        elif ai_difficulty == "medium":
            self.max_ball_speed = 5.0
        else:  
            self.max_ball_speed = None  
        
        
        self.paddle_left = Paddle(20, self.height//2 - 60, 20, 120, is_ai=False)
        self.paddle_right = Paddle(self.width - 40, self.height//2 - 60, 20, 120, 
                                 is_ai=True, ai_difficulty=ai_difficulty)
        self.ball = Ball(self.width//2 - 15, self.height//2 - 15, 30, 
                        max_speed=self.max_ball_speed, difficulty=ai_difficulty)
        
        
        self.game_over = False
        self.winner = None
        pygame.mouse.set_visible(False)
        
        
        try:
            self.paddle_sound = pygame.mixer.Sound('assets/paddle_hit.wav')
            self.score_sound = pygame.mixer.Sound('assets/score.wav')
            self.lose_sound = pygame.mixer.Sound('assets/lose.wav')
            
            self.powerup_sound = pygame.mixer.Sound('assets/powerup.wav')
            self.slowdown_sound = pygame.mixer.Sound('assets/slowdown.wav')
        except:
            print("Sound files not found")
            
        
        self.font = pygame.font.Font(None, 74)
        self.game_over_font = pygame.font.Font(None, 90)
        self.instruction_font = pygame.font.Font(None, 36)
        
        self.last_score = 0  
        self.total_score = 0  
        self.score_popup_timer = 0  
        
        
        from menu import Settings
        self.settings = Settings()
        
        
        self.ai_difficulty = ai_difficulty
        
        
        self.modifiers = []
        self.active_modifiers = {
            "paddle_size": {"active": False, "timer": 0, "duration": 20},  
            "ball_speed": {"active": False, "timer": 0, "duration": 10},   
            "extra_ball": {"active": False, "timer": 0, "duration": 5}     
        }
        self.extra_ball = None
        self.modifier_spawn_timer = 0
        self.modifier_spawn_interval = random.uniform(5, 7)  
        self.last_time = pygame.time.get_ticks()  

    def reset_game(self):
        
        self.width = self.screen.get_width()
        self.height = self.screen.get_height()
        
        
        self.paddle_left = Paddle(20, self.height//2 - 60, 20, 120, is_ai=False)
        self.paddle_right = Paddle(self.width - 40, self.height//2 - 60, 20, 120, 
                                 is_ai=True, ai_difficulty=self.ai_difficulty)
        
        self.paddle_left.alive = True
        self.paddle_right.alive = True
        self.paddle_left.score = 0
        self.paddle_right.score = 0
        self.total_score = 0  
        self.last_score = 0
        self.score_popup_timer = 0
        self.ball = Ball(self.width//2 - 15, self.height//2 - 15, 30, 
                        max_speed=self.max_ball_speed, difficulty=self.ai_difficulty)
        self.game_over = False
        self.winner = None
        pygame.mouse.set_visible(False)  

    def spawn_modifier(self):
        if len(self.modifiers) < 2:  
            x = random.randint(50, self.width - 50)
            y = random.randint(50, self.height - 50)
            modifier_type = random.choice(["paddle_size", "ball_speed", "extra_ball"])
            self.modifiers.append(GameModifier(x, y, modifier_type))
            
    def handle_modifiers(self):
        
        current_time = pygame.time.get_ticks()
        delta_time = (current_time - self.last_time) / 1000.0  
        self.last_time = current_time
        
        
        self.modifier_spawn_timer += delta_time
        if self.modifier_spawn_timer >= self.modifier_spawn_interval:
            self.spawn_modifier()
            self.modifier_spawn_timer = 0
            
            self.modifier_spawn_interval = random.uniform(5, 7)
            
        
        for modifier_type, data in self.active_modifiers.items():
            if data["active"]:
                data["timer"] -= delta_time
                if data["timer"] <= 0:
                    data["active"] = False
                    
                    if modifier_type == "paddle_size":
                        self.paddle_left.rect.height = 120  
                    elif modifier_type == "ball_speed":
                        self.ball.current_speed = self.ball.base_speed
                    elif modifier_type == "extra_ball":
                        self.extra_ball = None
                        
    def check_modifier_collisions(self):
        
        for modifier in self.modifiers[:]:
            if self.ball.rect.colliderect(modifier.rect):
                self.apply_modifier(modifier)
                self.modifiers.remove(modifier)
                try:
                    if modifier.type in ["paddle_size", "ball_speed"]:
                        self.powerup_sound.play()
                    else:
                        self.slowdown_sound.play()
                except:
                    pass
                    
        
        if self.extra_ball:
            for modifier in self.modifiers[:]:
                if self.extra_ball.rect.colliderect(modifier.rect):
                    self.modifiers.remove(modifier)
            
    def apply_modifier(self, modifier):
        if modifier.type == "paddle_size":
            self.active_modifiers["paddle_size"]["active"] = True
            self.active_modifiers["paddle_size"]["timer"] = self.active_modifiers["paddle_size"]["duration"]
            self.paddle_left.rect.height = 180  
        elif modifier.type == "ball_speed":
            self.active_modifiers["ball_speed"]["active"] = True
            self.active_modifiers["ball_speed"]["timer"] = self.active_modifiers["ball_speed"]["duration"]
            
            new_speed = max(0.1, self.ball.current_speed * 0.3)
            self.ball.current_speed = new_speed
        elif modifier.type == "extra_ball":
            self.active_modifiers["extra_ball"]["active"] = True
            self.active_modifiers["extra_ball"]["timer"] = self.active_modifiers["extra_ball"]["duration"]
            self.extra_ball = Ball(self.width//2 - 15, self.height//2 - 15, 30, 
                                 max_speed=self.max_ball_speed, difficulty=self.ai_difficulty)
            self.extra_ball.color = (255, 0, 0)  
            
    def run(self):
        while True:
            
            self.width = self.screen.get_width()
            self.height = self.screen.get_height()
            
            self.screen.fill((0, 0, 0))
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.mouse.set_visible(False)  
                        return "menu"
                    if event.key == pygame.K_SPACE and self.game_over:
                        self.reset_game()
                    if event.key == pygame.K_m and self.game_over:
                        pygame.mouse.set_visible(False)  
                        return "menu"
                    if event.key == pygame.K_t and self.game_over and self.winner == "Player":
                        pygame.mouse.set_visible(False)  
                        return f"scores:{self.total_score}"  
            
            if not self.game_over:
                
                mouse_y = pygame.mouse.get_pos()[1]
                self.paddle_left.move_to_mouse(mouse_y)
                
                
                keys = pygame.key.get_pressed()
                if keys[pygame.K_w] and self.paddle_left.alive:
                    self.paddle_left.move(up=True)
                if keys[pygame.K_s] and self.paddle_left.alive:
                    self.paddle_left.move(up=False)
                
                
                self.paddle_right.ai_move(self.ball, self.extra_ball)
                    
                
                self.ball.move()
                
                
                if self.ball.rect.top <= 0 or self.ball.rect.bottom >= self.height:
                    self.ball.bounce()
                    
                
                if self.ball.rect.colliderect(self.paddle_left.rect) and self.paddle_left.alive or \
                   self.ball.rect.colliderect(self.paddle_right.rect) and self.paddle_right.alive:
                    if self.ball.rect.colliderect(self.paddle_left.rect):
                        self.ball.bounce_paddle(is_left_paddle=True)
                        points = int((self.ball.current_speed * 102) / 2)
                        self.paddle_left.score += 1
                        self.total_score += points
                        self.last_score = points
                        self.score_popup_timer = 60  
                    else:
                        self.ball.bounce_paddle(is_left_paddle=False)
                        self.paddle_right.score += 1
                    try:
                        self.paddle_sound.play()
                    except:
                        pass
                    
                
                if self.ball.rect.left <= 0:
                    self.paddle_left.alive = False
                    self.game_over = True
                    self.winner = "AI"
                    pygame.mouse.set_visible(True)  
                    try:
                        self.lose_sound.play()
                    except:
                        pass
                        
                if self.ball.rect.right >= self.width:
                    self.paddle_right.alive = False
                    self.game_over = True
                    self.winner = "Player"
                    pygame.mouse.set_visible(True)  
                    try:
                        self.lose_sound.play()
                    except:
                        pass
                
                
                if self.extra_ball:
                    if self.extra_ball.rect.left <= 0:
                        self.paddle_left.alive = False
                        self.game_over = True
                        self.winner = "AI"
                        pygame.mouse.set_visible(True)  
                        try:
                            self.lose_sound.play()
                        except:
                            pass
                            
                    if self.extra_ball.rect.right >= self.width:
                        self.paddle_right.alive = False
                        self.game_over = True
                        self.winner = "Player"
                        pygame.mouse.set_visible(True)  
                        try:
                            self.lose_sound.play()
                        except:
                            pass

                
                self.handle_modifiers()
                self.check_modifier_collisions()
                
                
                if self.extra_ball:
                    self.extra_ball.move()
                    if self.extra_ball.rect.top <= 0 or self.extra_ball.rect.bottom >= self.height:
                        self.extra_ball.bounce()
                    if self.extra_ball.rect.colliderect(self.paddle_left.rect) and self.paddle_left.alive or \
                       self.extra_ball.rect.colliderect(self.paddle_right.rect) and self.paddle_right.alive:
                        if self.extra_ball.rect.colliderect(self.paddle_left.rect):
                            self.extra_ball.bounce_paddle(is_left_paddle=True)
                        else:
                            self.extra_ball.bounce_paddle(is_left_paddle=False)
                        try:
                            self.paddle_sound.play()
                        except:
                            pass

            
            antialiasing_enabled = self.settings.current_settings['antialiasing_enabled']
            
            
            self.paddle_left.draw(self.screen, antialiasing_enabled)
            self.paddle_right.draw(self.screen, antialiasing_enabled)
            self.ball.draw(self.screen, antialiasing_enabled)
            
            
            score_left = self.font.render(str(self.paddle_left.score), True, (255, 255, 255))
            score_right = self.font.render(str(self.paddle_right.score), True, (255, 255, 255))
            
            
            score_left_rect = score_left.get_rect(centerx=self.width//4, top=20)
            score_right_rect = score_right.get_rect(centerx=3*self.width//4, top=20)
            
            self.screen.blit(score_left, score_left_rect)
            self.screen.blit(score_right, score_right_rect)
            
            
            speed_text = self.instruction_font.render(
                f"Ball Speed: {self.ball.current_speed:.1f}", True, (255, 255, 255))
            speed_rect = speed_text.get_rect(centerx=self.width//2, top=20)
            self.screen.blit(speed_text, speed_rect)
            
            
            if self.max_ball_speed is not None:
                max_speed_text = self.instruction_font.render(
                    f"Max Speed: {self.max_ball_speed:.1f}", True, (200, 200, 200))
                max_speed_rect = max_speed_text.get_rect(centerx=self.width//2, top=50)
                self.screen.blit(max_speed_text, max_speed_rect)
            
            
            total_score_text = self.instruction_font.render(
                f"Total Score: {self.total_score}", True, (255, 255, 255))
            total_score_rect = total_score_text.get_rect(
                centerx=self.width//2,
                bottom=self.height - 20
            )
            self.screen.blit(total_score_text, total_score_rect)
            
            
            if self.score_popup_timer > 0:
                popup_color = (0, 255, 0)
                score_popup = self.instruction_font.render(
                    f"+{self.last_score}", True, popup_color)
                popup_rect = score_popup.get_rect(
                    centerx=self.width//2,
                    centery=self.height//2 - 50
                )
                
                alpha = int(255 * (self.score_popup_timer / 60))
                score_popup.set_alpha(alpha)
                self.screen.blit(score_popup, popup_rect)
                self.score_popup_timer -= 1
            
            
            if self.game_over:
                if self.winner == "Player":
                    
                    game_over_text = self.game_over_font.render("YOU WON!", True, (0, 255, 0))
                    final_score_text = self.font.render(f"Final Score: {self.total_score}", True, (255, 255, 255))
                    restart_text = self.instruction_font.render("Press SPACE to play again", True, (255, 255, 255))
                    menu_text = self.instruction_font.render("Press M to return to menu", True, (255, 255, 255))
                    scores_text = self.instruction_font.render("Press T to view global scores", True, (255, 255, 255))
                    name_text = self.instruction_font.render("Enter your name in the scores menu", True, (255, 255, 255))
                    
                    
                    game_over_rect = game_over_text.get_rect(centerx=self.width//2, centery=self.height//2 - 120)
                    final_score_rect = final_score_text.get_rect(centerx=self.width//2, centery=self.height//2 - 30)
                    restart_rect = restart_text.get_rect(centerx=self.width//2, centery=self.height//2 + 30)
                    menu_rect = menu_text.get_rect(centerx=self.width//2, centery=self.height//2 + 90)
                    scores_rect = scores_text.get_rect(centerx=self.width//2, centery=self.height//2 + 150)
                    name_rect = name_text.get_rect(centerx=self.width//2, centery=self.height//2 + 210)
                    
                    self.screen.blit(game_over_text, game_over_rect)
                    self.screen.blit(final_score_text, final_score_rect)
                    self.screen.blit(restart_text, restart_rect)
                    self.screen.blit(menu_text, menu_rect)
                    self.screen.blit(scores_text, scores_rect)
                    self.screen.blit(name_text, name_rect)
                else:
                    
                    game_over_text = self.game_over_font.render("GAME OVER", True, (255, 0, 0))
                    winner_text = self.font.render(f"{self.winner} Wins!", True, (255, 255, 255))
                    final_score_text = self.font.render(f"Final Score: {self.total_score}", True, (255, 255, 255))
                    restart_text = self.instruction_font.render("Press SPACE to restart", True, (255, 255, 255))
                    menu_text = self.instruction_font.render("Press M to go to main menu", True, (255, 255, 255))
                    
                    
                    game_over_rect = game_over_text.get_rect(centerx=self.width//2, centery=self.height//2 - 120)
                    winner_rect = winner_text.get_rect(centerx=self.width//2, centery=self.height//2 - 30)
                    final_score_rect = final_score_text.get_rect(centerx=self.width//2, centery=self.height//2 + 30)
                    restart_rect = restart_text.get_rect(centerx=self.width//2, centery=self.height//2 + 100)
                    menu_rect = menu_text.get_rect(centerx=self.width//2, centery=self.height//2 + 160)
                    
                    self.screen.blit(game_over_text, game_over_rect)
                    self.screen.blit(winner_text, winner_rect)
                    self.screen.blit(final_score_text, final_score_rect)
                    self.screen.blit(restart_text, restart_rect)
                    self.screen.blit(menu_text, menu_rect)
            
            
            if not self.game_over:
                mouse_pos = pygame.mouse.get_pos()
                
                if antialiasing_enabled:
                    circle_surface = pygame.Surface((6, 6), pygame.SRCALPHA)
                    pygame.draw.circle(circle_surface, (100, 100, 100, 255), (3, 3), 3)
                    self.screen.blit(circle_surface, 
                                   (self.paddle_left.rect.right + 10 - 3, mouse_pos[1] - 3))
                else:
                    pygame.draw.circle(self.screen, (100, 100, 100), 
                                     (self.paddle_left.rect.right + 10, mouse_pos[1]), 3)
            
            
            for modifier in self.modifiers:
                modifier.draw(self.screen, antialiasing_enabled)
            if self.extra_ball:
                self.extra_ball.draw(self.screen, antialiasing_enabled)
                
            
            y_offset = 80
            for modifier_type, data in self.active_modifiers.items():
                if data["active"]:
                    color = (255, 0, 0) if modifier_type in ["paddle_size", "ball_speed"] else (255, 255, 0)
                    text = self.instruction_font.render(
                        f"{modifier_type.replace('_', ' ').title()}: {data['timer']:.1f}s", 
                        True, color)
                    text_rect = text.get_rect(centerx=self.width//2, top=y_offset)
                    self.screen.blit(text, text_rect)
                    y_offset += 30
            
            pygame.display.flip() 