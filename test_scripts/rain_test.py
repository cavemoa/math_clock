import pygame
import random

# --- 1. Initialization & Settings ---
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Matrix Digital Rain - Visual Engine Test")
clock = pygame.time.Clock()

# --- 2. Typography & Colors ---
FONT_SIZE = 20
# Using Consolas or a fallback system monospace font for the hacker aesthetic
font = pygame.font.SysFont('consolas', FONT_SIZE, bold=True)

# The classic color palette
COLOR_HEAD = (200, 255, 200)  # Bright, nearly white green for the leading character
COLOR_TAIL = (0, 255, 0)      # Standard terminal green for the trail
BG_COLOR = (0, 0, 0)

# Characters to pull from (Alphanumeric and symbols work best universally)
matrix_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%^&*"

# --- 3. The "Fade" Surface ---
# We draw this over the screen every frame to slowly fade old characters to black
fade_surface = pygame.Surface((WIDTH, HEIGHT))
fade_surface.fill(BG_COLOR)
fade_surface.set_alpha(15) # Lower is a longer trail, higher is a shorter trail

# --- 4. Grid Setup ---
columns = WIDTH // FONT_SIZE
# This list holds the current Y-coordinate (in grid rows, not pixels) for each column.
# We start them at random negative values so they don't all fall at once.
drops = [random.randint(-50, 0) for _ in range(columns)]

# --- 5. Main Game Loop ---
running = True
while running:
    # Event handling (allows you to close the window)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

    # Apply the fade effect over the entire screen
    screen.blit(fade_surface, (0, 0))

    # Process each column
    for i in range(len(drops)):
        # Calculate X and Y pixel coordinates
        x = i * FONT_SIZE
        y = drops[i] * FONT_SIZE
        
        # Pick a random character for the leading "head"
        char = random.choice(matrix_chars)
        char_render = font.render(char, True, COLOR_HEAD)
        screen.blit(char_render, (x, y))

        # To make it look like the characters are flipping, we draw a standard
        # green character right above the head to act as the start of the trail.
        if drops[i] > 0:
            trail_char = random.choice(matrix_chars)
            trail_render = font.render(trail_char, True, COLOR_TAIL)
            screen.blit(trail_render, (x, y - FONT_SIZE))

        # Move the drop down one row for the next frame
        drops[i] += 1

        # Reset the drop to the top randomly once it hits the bottom
        # The random check prevents a straight horizontal line of resets
        if y > HEIGHT and random.random() > 0.95:
            drops[i] = 0

    # Update the display
    pygame.display.flip()
    
    # Cap the framerate. 30 FPS gives it that slightly jittery, retro terminal feel.
    clock.tick(30)

pygame.quit()