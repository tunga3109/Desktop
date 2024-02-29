import pygame
import random
import sys

# Инициализация Pygame
pygame.init()

# Определение экрана
screen_width = 400
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Flappy Bird")

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)


bird_image = pygame.image.load("pngegg.png")
bird_image = pygame.transform.scale(bird_image, (100, 90))
bird_rect = bird_image.get_rect()

# Игровые параметры
gravity = 0.25
bird_movement = 0
bird_y = screen_height // 2
bird_radius = 20
bird_color = BLACK

# Трубы
pipe_width = 50
pipe_gap = 150
pipe_x = screen_width
pipe_height = 300
pipe_color = GREEN
pipe_speed = 2
pipes = []

pipe_image = pygame.image.load("Free Download.jpeg")
pipe_image = pygame.transform.scale(pipe_image, (pipe_width, pipe_height))  # Уменьшаем размер в соответствии с pipe_width и pipe_height
pipe_rect = pipe_image.get_rect()

# Создание птицы
def draw_bird():
    screen.blit(bird_image, (int(screen_width / 3), int(bird_y)))

# Создание труб
def draw_pipes():
    for pipe in pipes:
        screen.blit(pipe_image, (pipe[0], pipe[1]))

# Проверка столкновения
def check_collision():
    for pipe in pipes:
        if pipe[0] < bird_radius * 2 and bird_y < pipe[1] + pipe[3] and bird_y > pipe[1]:
            return True
        if pipe[0] < bird_radius * 2 and (bird_y + bird_radius) > pipe[1] + pipe[3] + pipe_gap:
            return True
    if bird_y > screen_height or bird_y < 0:
        return True
    return False

# Основной игровой цикл
clock = pygame.time.Clock()
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                bird_movement = 0
                bird_movement -= 7

    # Движение птицы
    bird_movement += gravity
    bird_y += bird_movement

    # Генерация новых труб
    if len(pipes) < 2:
        pipe_height = random.randint(150, 400)
        new_pipe = [screen_width, 0, pipe_width, pipe_height]
        pipes.append(new_pipe)
        new_pipe = [screen_width, pipe_height + pipe_gap, pipe_width, screen_height - pipe_height - pipe_gap]
        pipes.append(new_pipe)

    # Движение труб
    for pipe in pipes:
        pipe[0] -= pipe_speed

    # Удаление труб за пределами экрана
    pipes = [pipe for pipe in pipes if pipe[0] > -pipe_width]

    # Проверка столкновения
    if check_collision():
        print("Game Over!")
        pipes = []
        bird_y = screen_height // 2
        bird_movement = 0

    # Отрисовка экрана
    screen.fill(WHITE)
    draw_bird()
    draw_pipes()
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
