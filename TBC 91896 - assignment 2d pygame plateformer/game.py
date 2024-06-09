"""
-----------------------------------------
    Project: Windows 95 game
    Standard: 91896 (AS2.7) V.2
    Python: 3.12.3
-----------------------------------------
"""
#importing 
import pygame
from pygame.locals import *
from pygame import mixer
import os
import pickle
from os import path
import time

# Initialize Pygame and mixer
pygame.mixer.pre_init(44100, -16, 2, 512)
mixer.init()
pygame.init()

clock = pygame.time.Clock()  # Create a clock object to control the frame rate
fps = 60  # Set the frames per second

# Define screen dimensions
screen_width = 1000
screen_height = 1000

# Create the game window
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Windows 95 Man')

# Define fonts
font = pygame.font.SysFont('Bauhaus 93', 70)
font_score = pygame.font.SysFont('Bauhaus 93', 30)

# Define game variables
tile_size = 50
game_over = 0
main_menu = True
level = 0
max_levels = 2
score = 0
coin_picked_up = 0
start_time = 0
high_score = float('inf')
level_cap = 0

# Define colors
blue = (0, 0, 255)

# Load images
bg_img = pygame.image.load('img/background.png')
restart_img = pygame.image.load('img/restart_btn.png')
start_img = pygame.image.load('img/start_btn.png')
exit_img = pygame.image.load('img/exit_btn.png')

# Load sounds
pygame.mixer.music.load('img/music.wav')
pygame.mixer.music.play(-1, 0.0, 5000)
coin_fx = pygame.mixer.Sound('img/coin.wav')
coin_fx.set_volume(0.5)
jump_fx = pygame.mixer.Sound('img/jump.wav')
jump_fx.set_volume(0.5)
game_over_fx = pygame.mixer.Sound('img/game_over.wav')
game_over_fx.set_volume(0.5)

# Function to draw text on the screen
def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))
 
# Load the high score from a file
def load_high_score():
    if os.path.exists('high_score.txt'):
        with open('high_score.txt', 'r') as file:
            try:
                return float(file.read().strip())
            except ValueError:
                return 0
    return 0

# Save the high score to a file
def save_high_score(high_score):
    with open('high_score.txt', 'w') as file:
        file.write(str(high_score))

# Redefine the draw_text function (redundant, already defined above)
def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

# Load and display the high score
high_score = int(load_high_score())
high_score_text = pygame.font.Font(None, 36).render(f"High Score: {high_score}", True, (255, 255, 255)) 
screen.blit(high_score_text, (10, 50))

# Function to reset the level
def reset_level(level):
    player.reset(100, screen_height - 130)
    spike_group.empty()
    platform_group.empty()
    coin_group.empty()
    lava_group.empty()
    exit_group.empty()

    # Load level data and create the world
    if path.exists(f'level{level}_data'):
        pickle_in = open(f'level{level}_data', 'rb')
        world_data = pickle.load(pickle_in)
    world = World(world_data)
    # Create a dummy coin to show the score
    score_coin = Coin(tile_size // 2, tile_size // 2)
    coin_group.add(score_coin)
    return world

# Button class
class Button():
    def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.clicked = False

    def draw(self):
        action = False
        # Get mouse position
        pos = pygame.mouse.get_pos()
        # Check if the mouse is over the button and if it is clicked
        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
                action = True
                self.clicked = True
        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False
        # Draw button
        screen.blit(self.image, self.rect)
        return action

# Player class
class Player():
    def __init__(self, x, y):
        self.reset(x, y)
        self.moving_left = False
        self.moving_right = False
        self.flip = False

    def update(self, game_over):
        dx = 0
        dy = 0
        walk_cooldown = 5

        if game_over == 0:
            # Get keypresses
            key = pygame.key.get_pressed()
            if key[pygame.K_UP] and self.jumped == False and self.in_air == False:
                jump_fx.play()
                self.vel_y = -20
                self.jumped = True
                self.update_action(2)  # Jump animation
            if key[pygame.K_UP] == False:
                self.jumped = False
            if key[pygame.K_LEFT]:
                dx -= 5
                self.counter += 1
                self.direction = 1
                self.update_action(1)  # Run animation
            if key[pygame.K_RIGHT]:
                dx += 5
                self.counter += 1
                self.direction = -1
                self.update_action(1)  # Run animation
            if key[pygame.K_LEFT] == False and key[pygame.K_RIGHT] == False and not self.jumped:
                self.counter = 0
                self.index = 0
                self.update_action(0)  # Idle animation

            # Handle animation
            self.update_animation()

            # Add gravity
            self.vel_y += 1
            if self.vel_y > 10:
                self.vel_y = 10
            dy += self.vel_y

            # Check for collision
            self.in_air = True
            for tile in world.tile_list:
                # Check for collision in x direction
                if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    dx = 0
                # Check for collision in y direction
                if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                    # Check if below the ground (jumping)
                    if self.vel_y < 0:
                        dy = tile[1].bottom - self.rect.top
                        self.vel_y = 0
                    # Check if above the ground (falling)
                    elif self.vel_y >= 0:
                        dy = tile[1].top - self.rect.bottom
                        self.vel_y = 0
                        self.in_air = False

            # Check for collision with enemies
            if pygame.sprite.spritecollide(self, spike_group, False):
                game_over = -1
                game_over_fx.play()

            # Check for collision with lava
            if pygame.sprite.spritecollide(self, lava_group, False):
                game_over = -1
                game_over_fx.play()

            # Check for collision with exit
            if pygame.sprite.spritecollide(self, exit_group, False) and coin_picked_up:
                game_over = 1

            # Check for collision with platforms
            for platform in platform_group:
                # Collision in the x direction
                if platform.rect.colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    dx = 0
                # Collision in the y direction
                if platform.rect.colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                    # Check if below platform
                    if abs((self.rect.top + dy) - platform.rect.bottom) < 20:
                        self.vel_y = 0
                        dy = platform.rect.bottom - self.rect.top
                    # Check if above platform
                    elif abs((self.rect.bottom + dy) - platform.rect.top) < 20:
                        self.rect.bottom = platform.rect.top - 1
                        self.in_air = False
                        dy = 0
                    # Move sideways with the platform
                    if platform.move_x != 0:
                        self.rect.x += platform.move_direction

            # Update player coordinates
            self.rect.x += dx
            self.rect.y += dy

        elif game_over == -1:
            self.update_action(3)  # Death animation
            draw_text('GAME OVER!', font, blue, (screen_width // 2) - 200, screen_height // 2)
            if self.rect.y > 200:
                self.rect.y -= 5

        # Draw player onto screen
        screen.blit(pygame.transform.flip(self.image, self.direction == -1, False), self.rect)

        return game_over

    def reset(self, x, y):
        self.animation_list = []
        self.action = 0  # 0: idle, 1: run, 2: jump, 3: death
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()

        animation_types = ['Idle', 'Run', 'Jump', 'Death']
        for animation in animation_types:
            # Reset temporary list of images
            temp_list = []
            # count number of files in the folder
            num_of_frames = len(os.listdir(f'img/{animation}'))
            for i in range(num_of_frames):
                img = pygame.image.load(f'img/{animation}/{i}.png').convert_alpha()
                img = pygame.transform.scale(img, (int(img.get_width() * 2 ), int(img.get_height() * 2)))
                temp_list.append(img)
            self.animation_list.append(temp_list)

        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.vel_y = 0
        self.jumped = False
        self.direction = 0
        self.in_air = True
        self.counter = 0
        self.index = 0
        self.update_time = pygame.time.get_ticks()

    def update_animation(self):
        # update animation
        ANIMATION_COOLDOWN = 200
        # update image
        self.image = self.animation_list[self.action][self.frame_index]
        # check if enough time has passed since the last update
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
        # reset animation
        if self.frame_index >= len(self.animation_list[self.action]):
            if self.action == 3:
                self.frame_index = len(self.animation_list[self.action]) - 1
            else:
                self.frame_index = 0

    def update_action(self, new_action):
        # check if the new action is different to the previous one
        if new_action != self.action:
            self.action = new_action
            # update the animation settings
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()



class World():
	def __init__(self, data):
		self.tile_list = []

		#load images
		dirt_img = pygame.image.load('img/dirt.png')
		grass_img = pygame.image.load('img/grass.png')

		row_count = 0
		for row in data:
			col_count = 0
			for tile in row:
				if tile == 1:
					img = pygame.transform.scale(dirt_img, (tile_size, tile_size))
					img_rect = img.get_rect()
					img_rect.x = col_count * tile_size
					img_rect.y = row_count * tile_size
					tile = (img, img_rect)
					self.tile_list.append(tile)
				if tile == 2:
					img = pygame.transform.scale(grass_img, (tile_size, tile_size))
					img_rect = img.get_rect()
					img_rect.x = col_count * tile_size
					img_rect.y = row_count * tile_size
					tile = (img, img_rect)
					self.tile_list.append(tile)
				if tile == 3:
					spike = Enemy(col_count * tile_size, row_count * tile_size - 15)
					spike_group.add(spike)
				if tile == 4:
					platform = Platform(col_count * tile_size, row_count * tile_size, 1, 0)
					platform_group.add(platform)
				if tile == 5:
					platform = Platform(col_count * tile_size, row_count * tile_size, 0, 1)
					platform_group.add(platform)
				if tile == 6:
					lava = Lava(col_count * tile_size, row_count * tile_size + (tile_size // 2))
					lava_group.add(lava)
				if tile == 7:
					coin = Coin(col_count * tile_size + (tile_size // 2), row_count * tile_size + (tile_size // 2))
					coin_group.add(coin)
				if tile == 8:
					exit = Exit(col_count * tile_size, row_count * tile_size - (tile_size // 2))
					exit_group.add(exit)
				col_count += 1
			row_count += 1


	def draw(self):
		for tile in self.tile_list:
			screen.blit(tile[0], tile[1])



class Enemy(pygame.sprite.Sprite):
	def __init__(self, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.image = pygame.image.load('img/spike head.png')
		self.rect = self.image.get_rect()
		self.rect.x = x
		self.rect.y = y
		self.move_direction = 1
		self.move_counter = 0

	def update(self):
		self.rect.x += self.move_direction
		self.move_counter += 1
		if abs(self.move_counter) > 50:
			self.move_direction *= -1
			self.move_counter *= -1


class Platform(pygame.sprite.Sprite):
	def __init__(self, x, y, move_x, move_y):
		pygame.sprite.Sprite.__init__(self)
		img = pygame.image.load('img/platform.png')
		self.image = pygame.transform.scale(img, (tile_size, tile_size // 2))
		self.rect = self.image.get_rect()
		self.rect.x = x
		self.rect.y = y
		self.move_counter = 0
		self.move_direction = 1
		self.move_x = move_x
		self.move_y = move_y








class Lava(pygame.sprite.Sprite):
	def __init__(self, x, y):
		pygame.sprite.Sprite.__init__(self)
		img = pygame.image.load('img/lava.png')
		self.image = pygame.transform.scale(img, (tile_size, tile_size // 2))
		self.rect = self.image.get_rect()
		self.rect.x = x
		self.rect.y = y


class Coin(pygame.sprite.Sprite):
	def __init__(self, x, y):
		pygame.sprite.Sprite.__init__(self)
		img = pygame.image.load('img/coin.png')
		self.image = pygame.transform.scale(img, (tile_size // 2, tile_size // 2))
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)


class Exit(pygame.sprite.Sprite):
	def __init__(self, x, y):
		pygame.sprite.Sprite.__init__(self)
		img = pygame.image.load('img/exit.png')
		self.image = pygame.transform.scale(img, (tile_size, int(tile_size * 1.5)))
		self.rect = self.image.get_rect()
		self.rect.x = x
		self.rect.y = y



player = Player(100, screen_height - 130)

spike_group = pygame.sprite.Group()
platform_group = pygame.sprite.Group()
lava_group = pygame.sprite.Group()
coin_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()

#create dummy coin for showing the score
score_coin = Coin(tile_size // 2, tile_size // 2)
coin_group.add(score_coin)

#load in level data and create world
if path.exists(f'level{level}_data'):
	pickle_in = open(f'level{level}_data', 'rb')
	world_data = pickle.load(pickle_in)
world = World(world_data)


#create buttons
restart_button = Button(screen_width // 2 - 100, screen_height // 2 + 100, restart_img)
start_button = Button(screen_width // 2 - 350, screen_height // 2, start_img)
exit_button = Button(screen_width // 2 + 150, screen_height // 2, exit_img)


run = True
while run:

    clock.tick(fps)

    screen.blit(bg_img, (0, 0))

    if main_menu:
        if exit_button.draw():
            run = False
        if start_button.draw():
            main_menu = False
            start_time = time.time()  # Start the timer
        # Display high score if it's not infinity
        if high_score != float('inf'):
            draw_text(f'Best Time: {high_score:.2f} seconds', font_score, blue, 350, 300)
    else:
        world.draw()

        if game_over == 0:
            current_time = time.time() - start_time  # Calculate current elapsed time
            draw_text(f'Time: {current_time:.2f} seconds', font_score, blue, 20, 50)  # Display current time
            draw_text(f'Best Time: {high_score:.2f} seconds', font_score, blue, 20, 75)
            

            spike_group.update()
            platform_group.update()
            # Update score
            # Check if a coin has been collected
            if pygame.sprite.spritecollide(player, coin_group, True):
                coin_fx.play()
                coin_picked_up += 1
                score += 1


            draw_text('X ' + str(score), font_score, blue, tile_size - 10, 10) 
        
        spike_group.draw(screen)
        platform_group.draw(screen)
        lava_group.draw(screen)
        coin_group.draw(screen)
        exit_group.draw(screen)
        
        game_over = player.update(game_over)

		#if player has died
        if game_over == -1:
            if restart_button.draw():
                world_data = []
                world = reset_level(level)
                game_over = 0
                score = 0

		#if player has completed the level
        if game_over == 1:
			#reset game and go to next level
            level += 1
            level_cap += 1
            if level <= max_levels:
				#reset level
                world_data = []
                world = reset_level(level)
                game_over = 0
            else:
                draw_text('YOU WIN!', font, blue, (screen_width // 2) - 140, screen_height // 2)
                if restart_button.draw():
                    level = 0
					#reset level
                    world_data = []
                    world = reset_level(level)
                    game_over = 0
                    score = 0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
   
    pygame.display.update()

pygame.quit()