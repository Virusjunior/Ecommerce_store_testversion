import pygame
import random

# Initialize Pygame
pygame.init()

# Set up the display
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Hangman")

# Set up fonts and colors
FONT = pygame.font.Font(None, 48)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Load the hangman images
hangman_images = []
for i in range(6):
    hangman_images.append(pygame.image.load(f"hangman{i}.png"))

# Set up the game variables
words_to_guess = ["january", "border", "image", "film", "promise", "kids", "lungs", "doll", "rhyme", "damage", "plants"]
word = random.choice(words_to_guess)
length = len(word)
display = "_" * length
already_guessed = []

# Set up the game loop
game_over = False
clock = pygame.time.Clock()

while not game_over:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_over = True
        elif event.type == pygame.KEYDOWN:
            if event.unicode.isalpha():
                guess = event.unicode.lower()
                if guess in already_guessed:
                    continue
                already_guessed.append(guess)
                if guess in word:
                    for i in range(length):
                        if word[i] == guess:
                            display = display[:i] + guess + display[i+1:]
                else:
                    if len(already_guessed) >= 6:
                        game_over = True

    # Draw the hangman and the word
    screen.fill(WHITE)
    screen.blit(hangman_images[len(already_guessed)], (0, 0))
    word_surface = FONT.render(display, True, BLACK)
    screen.blit(word_surface, (SCREEN_WIDTH//2 - word_surface.get_width()//2, SCREEN_HEIGHT//2))
    pygame.display.flip()

    # Check if the player has won or lost
    if display == word:
        game_over = True
        message_surface = FONT.render("You Win!", True, BLACK)
        screen.blit(message_surface, (SCREEN_WIDTH//2 - message_surface.get_width()//2, SCREEN_HEIGHT//2 + 50))
        pygame.display.flip()
        pygame.time.wait(3000)
    elif game_over:
        message_surface = FONT.render("You Lose!", True, BLACK)
        screen.blit(message_surface, (SCREEN_WIDTH//2 - message_surface.get_width()//2, SCREEN_HEIGHT//2 + 50))
        pygame.display.flip()
        pygame.time.wait(3000)

# Clean up
pygame.quit()