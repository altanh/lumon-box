import pygame
import sys
import random
import time
import math

# Initialize pygame
pygame.init()

# Constants
GRID_WIDTH = 17
GRID_HEIGHT = 10
CELL_SIZE = 50
MARGIN = 5
TIME_LIMIT = 120 # seconds

# Calculated constants
SCREEN_WIDTH = GRID_WIDTH * (CELL_SIZE + MARGIN) + MARGIN
SCREEN_HEIGHT = GRID_HEIGHT * (CELL_SIZE + MARGIN) + MARGIN + 100  # Extra space for score and timer

# Colors
WHITE = (104, 238, 247)
BLACK = (8, 51, 54)
GRAY = (50, 50, 50)  # Darker gray for empty cells
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
TIMER_BG = (15, 96, 102)  # Background color for timer bar
TIMER_COLOR = WHITE #(0, 191, 255)  # Color for timer bar

# Create the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Lumon Box")

# Font setup
FONT = None
font = pygame.font.SysFont(FONT, 36)
small_font = pygame.font.SysFont(FONT, 24)

class AnimatedNumber:
    def __init__(self, value, x, y, target_x, target_y):
        self.value = value
        self.x = x
        self.y = y
        self.target_x = target_x
        self.target_y = target_y
        self.speed = random.uniform(8, 15)
        self.scale = 1.0
        self.alpha = 255
        self.lifetime = 0
        # Calculate angle towards target
        dx = target_x - x
        dy = target_y - y
        self.angle = math.atan2(dy, dx)
        
    def update(self):
        # Update position
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        
        # Update properties
        self.lifetime += 1
        self.scale -= 0.03
        self.alpha -= 5
        
        # Return True if animation should continue
        return self.scale > 0 and self.alpha > 0

class Game:
    def __init__(self):
        self.grid = [[random.randint(1, 9) for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.score = 0
        self.start_time = time.time()
        self.selection_start = None
        self.selection_end = None
        self.selecting = False
        self.animated_numbers = []  # List to hold animated numbers
        self.jiggle_offsets = [
            [(random.uniform(0, 100), random.uniform(0, 100)) for _ in range(GRID_WIDTH)]
            for _ in range(GRID_HEIGHT)
        ] 

    def reset(self):
        self.grid = [[random.randint(1, 9) for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.score = 0
        self.start_time = time.time()
        self.selection_start = None
        self.selection_end = None
        self.selecting = False
        self.animated_numbers = []
        self.jiggle_offsets = [
            [(random.uniform(0, 100), random.uniform(0, 100)) for _ in range(GRID_WIDTH)]
            for _ in range(GRID_HEIGHT)
        ] 

    def get_remaining_time(self):
        elapsed = time.time() - self.start_time
        remaining = max(0, TIME_LIMIT - elapsed)
        return remaining
    
    def is_game_over(self):
        return self.get_remaining_time() <= 0
    
    def get_cell_at_pos(self, pos):
        x, y = pos
        grid_x = (x - MARGIN) // (CELL_SIZE + MARGIN)
        grid_y = (y - MARGIN) // (CELL_SIZE + MARGIN)
        
        if 0 <= grid_x < GRID_WIDTH and 0 <= grid_y < GRID_HEIGHT:
            return (grid_x, grid_y)
        return None
    
    def get_selection_rect(self):
        if not self.selection_start or not self.selection_end:
            return None
        
        x1, y1 = self.selection_start
        x2, y2 = self.selection_end
        
        # Ensure x1,y1 is the top-left corner and x2,y2 is the bottom-right
        x1, x2 = min(x1, x2), max(x1, x2)
        y1, y2 = min(y1, y2), max(y1, y2)
        
        return (x1, y1, x2, y2)
    
    def calculate_selection_sum(self):
        if not self.selection_start or not self.selection_end:
            return 0
        
        rect = self.get_selection_rect()
        if not rect:
            return 0
        
        x1, y1, x2, y2 = rect
        selection_sum = 0
        count = 0
        
        for y in range(y1, y2 + 1):
            for x in range(x1, x2 + 1):
                if self.grid[y][x] > 0:  # Only count non-zero cells
                    selection_sum += self.grid[y][x]
                    count += 1
        
        return selection_sum, count
    
    def clear_selection(self):
        if not self.selection_start or not self.selection_end:
            return False
        
        selection_sum, count = self.calculate_selection_sum()
        
        if selection_sum == 10:
            rect = self.get_selection_rect()
            x1, y1, x2, y2 = rect
            
            # Calculate the center of the selection for animation effect
            center_x = MARGIN + ((x1 + x2) / 2) * (CELL_SIZE + MARGIN) + CELL_SIZE / 2
            center_y = MARGIN + ((y1 + y2) / 2) * (CELL_SIZE + MARGIN) + CELL_SIZE / 2
            
            # Calculate a "pull" point outside the screen (in the direction of the center of the screen)
            screen_center_x = SCREEN_WIDTH / 2
            screen_center_y = SCREEN_HEIGHT / 2
            
            # Direction vector from screen center to selection center
            dir_x = center_x - screen_center_x
            dir_y = center_y - screen_center_y
            
            # Normalize and reverse to get pull direction
            length = math.sqrt(dir_x * dir_x + dir_y * dir_y)
            if length > 0:
                pull_x = screen_center_x - dir_x / length * SCREEN_WIDTH
                pull_y = screen_center_y - dir_y / length * SCREEN_HEIGHT
            else:
                # If selection is at screen center, pull to bottom
                pull_x = screen_center_x
                pull_y = SCREEN_HEIGHT * 2
            
            # Remove all selected numbers (set to 0) and create animations
            for y in range(y1, y2 + 1):
                for x in range(x1, x2 + 1):
                    if self.grid[y][x] > 0:  # Only clear non-zero cells
                        # Create animated number object for this cell
                        cell_x = MARGIN + x * (CELL_SIZE + MARGIN) + CELL_SIZE / 2
                        cell_y = MARGIN + y * (CELL_SIZE + MARGIN) + CELL_SIZE / 2
                        
                        # Add the animated number
                        animated_num = AnimatedNumber(
                            self.grid[y][x], 
                            cell_x, 
                            cell_y, 
                            pull_x, 
                            pull_y
                        )
                        self.animated_numbers.append(animated_num)
                        
                        # Set cell to 0
                        self.grid[y][x] = 0
            
            # Increase score by the count of cleared cells
            self.score += count
            return True
        
        return False
        
    def update_animations(self):
        # Update and filter out completed animations
        self.animated_numbers = [anim for anim in self.animated_numbers if anim.update()]


def draw_grid(game):
    # Get the current mouse position for the magnifying and jiggle effects
    mouse_x, mouse_y = pygame.mouse.get_pos()
    # Get current time for jiggle animation
    current_time = time.time()
    
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            # Calculate rectangle position
            rect_x = MARGIN + x * (CELL_SIZE + MARGIN)
            rect_y = MARGIN + y * (CELL_SIZE + MARGIN)
            
            # Draw cell background
            cell_color = BLACK
            pygame.draw.rect(screen, cell_color, [rect_x, rect_y, CELL_SIZE, CELL_SIZE])
            
            # Draw number if not zero
            if game.grid[y][x] > 0:
                # Calculate the center of the cell
                center_x = rect_x + CELL_SIZE // 2
                center_y = rect_y + CELL_SIZE // 2
                
                # Calculate distance from mouse cursor to the center of this cell
                distance = ((center_x - mouse_x) ** 2 + (center_y - mouse_y) ** 2) ** 0.5
                
                # Set maximum enlargement factor and effect radius
                max_scale = 2.0  # Maximum size increase
                effect_radius = 150  # How far the effect extends
                
                # Calculate scale factor based on distance (tapers off gradually)
                if distance < effect_radius:
                    # Scale decreases linearly with distance
                    scale_factor = max_scale - (distance / effect_radius) * (max_scale - 1.0)
                    scale_factor = max(1.0, min(max_scale, scale_factor))  # Clamp between 1.0 and max_scale
                    
                    # Add jiggle effect for numbers under cursor
                    jiggle_amplitude = 3.0  # Maximum pixel offset for jiggle
                    jiggle_speed = 3.0  # Speed of jiggle animation
                    
                    # Calculate jiggle offset based on distance from cursor
                    # The closer to cursor, the stronger the jiggle
                    jiggle_factor = (1 - distance / effect_radius) * jiggle_amplitude
                    
                    # Get the unique offset for this cell
                    offset_x, offset_y = game.jiggle_offsets[y][x]
                    
                    # Use unique offset to create independent jiggle motion for each number
                    jiggle_x = math.sin(current_time * jiggle_speed + offset_x) * jiggle_factor
                    jiggle_y = math.cos(current_time * jiggle_speed * 1.3 + offset_y) * jiggle_factor
                    
                    # Add tiny randomness for extra organic feel
                    jiggle_x += random.uniform(-0.2, 0.2) * jiggle_factor * 0.3
                    jiggle_y += random.uniform(-0.2, 0.2) * jiggle_factor * 0.3
                else:
                    scale_factor = 1.0  # No scaling beyond the effect radius
                    jiggle_x = 0
                    jiggle_y = 0
                
                # Create a font with the scaled size
                scaled_size = int(36 * scale_factor)  # Base font size is 36
                scaled_font = pygame.font.SysFont(FONT, scaled_size)
                
                # Render the number with the scaled font
                number_text = scaled_font.render(str(game.grid[y][x]), True, WHITE)
                text_rect = number_text.get_rect(center=(center_x + jiggle_x, center_y + jiggle_y))
                screen.blit(number_text, text_rect)


def draw_selection(game):
    if game.selection_start and game.selection_end:
        rect = game.get_selection_rect()
        if rect:
            x1, y1, x2, y2 = rect
            
            selection_sum, _ = game.calculate_selection_sum()
            color = WHITE #GREEN if selection_sum == 10 else RED
            
            # Draw rectangle around selection
            start_x = MARGIN + x1 * (CELL_SIZE + MARGIN)
            start_y = MARGIN + y1 * (CELL_SIZE + MARGIN)
            width = (x2 - x1 + 1) * (CELL_SIZE + MARGIN) - MARGIN
            height = (y2 - y1 + 1) * (CELL_SIZE + MARGIN) - MARGIN
            
            pygame.draw.rect(screen, color, [start_x, start_y, width, height], 3)
            
            # Display the sum
            #sum_text = small_font.render(f"Sum: {selection_sum}", True, WHITE)
            #screen.blit(sum_text, (start_x, start_y - 20))

def draw_animated_numbers(game):
    for anim in game.animated_numbers:
        # Calculate font size
        scaled_size = int(36 * anim.scale)
        if scaled_size < 10:  # Skip rendering very small numbers
            continue
            
        # Create font and render number
        anim_font = pygame.font.SysFont(FONT, scaled_size)
        
        # Set alpha for fading effect
        surf = anim_font.render(str(anim.value), True, WHITE)
        surf.set_alpha(anim.alpha)
        
        # Draw the animated number
        text_rect = surf.get_rect(center=(anim.x, anim.y))
        screen.blit(surf, text_rect)

def draw_ui(game):
    # Draw score
    progress = 100 * game.score / (GRID_WIDTH * GRID_HEIGHT)
    score_text = font.render(f"Progress: {game.score:.0f}%", True, WHITE)
    screen.blit(score_text, (20, SCREEN_HEIGHT - 80))
    
    # Draw timer as a bar
    remaining = game.get_remaining_time()
    timer_percentage = remaining / TIME_LIMIT
    
    # Timer bar background
    timer_bg_rect = pygame.Rect(20, SCREEN_HEIGHT - 50, SCREEN_WIDTH - 40, 20)
    pygame.draw.rect(screen, TIMER_BG, timer_bg_rect)
    
    # Timer bar foreground (decreasing)
    timer_width = int((SCREEN_WIDTH - 40) * timer_percentage)
    timer_rect = pygame.Rect(20, SCREEN_HEIGHT - 50, timer_width, 20)
    pygame.draw.rect(screen, TIMER_COLOR, timer_rect)
    
    # Draw game over modal if time is up
    if game.is_game_over():
        # Create semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Dark background with alpha
        screen.blit(overlay, (0, 0))
        
        # Calculate modal box dimensions
        modal_width = 400
        modal_height = 200
        modal_x = (SCREEN_WIDTH - modal_width) // 2
        modal_y = (SCREEN_HEIGHT - modal_height) // 2
        
        # Draw modal box with light frame
        pygame.draw.rect(screen, BLACK, [modal_x, modal_y, modal_width, modal_height])  # Dark background
        pygame.draw.rect(screen, WHITE, [modal_x, modal_y, modal_width, modal_height], 3)  # Light frame
        
        # Draw game over text
        game_over_text = font.render("GAME OVER", True, WHITE)
        text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, modal_y + 60))
        screen.blit(game_over_text, text_rect)
        
        # Draw score text
        score_text = font.render(f"Final Progress: {game.score}%", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, modal_y + 100))
        screen.blit(score_text, score_rect)
        
        # Draw restart instruction
        restart_text = small_font.render("Press 'R' to restart", True, WHITE)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, modal_y + 140))
        screen.blit(restart_text, restart_rect)

def main():
    game = Game()
    clock = pygame.time.Clock()
    
    # Game loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Handle key presses
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  # Reset game when 'R' is pressed
                    game.reset()
            
            # Handle mouse events if game is not over
            elif not game.is_game_over():
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left mouse button
                    cell = game.get_cell_at_pos(event.pos)
                    if cell:
                        game.selection_start = cell
                        game.selection_end = cell
                        game.selecting = True
                
                elif event.type == pygame.MOUSEMOTION and game.selecting:
                    cell = game.get_cell_at_pos(event.pos)
                    if cell:
                        game.selection_end = cell
                
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    game.selecting = False
                    if game.selection_start and game.selection_end:
                        game.clear_selection()
                        # Reset selection after processing
                        game.selection_start = None
                        game.selection_end = None
        
        # Update animations
        game.update_animations()
        
        # Fill the background
        screen.fill(BLACK)  # Keep the entire background black
        
        # Draw the game elements
        draw_grid(game)
        draw_selection(game)
        draw_animated_numbers(game)  # Draw animated numbers
        draw_ui(game)
        
        # Update the display
        pygame.display.flip()
        
        # Cap the frame rate
        clock.tick(60)
    
    # Quit pygame
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
