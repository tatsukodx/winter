import pygame
pygame.init()
screen = pygame.display.set_mode((400, 300))
print("pygame 起動成功")

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()