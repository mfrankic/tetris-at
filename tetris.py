#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Very simple tetris implementation
#
# Control keys:
#       Down - Drop stone faster
# Left/Right - Move stone
#         Up - Rotate Stone clockwise
#     Escape - Quit game
#          P - Pause game
#     Return - Instant drop
#
# Have fun!

import os
import sys
from random import randrange as rand

import pygame
from screeninfo import get_monitors

primary_monitor = [monitor for monitor in get_monitors()
                   if monitor.is_primary][0]

# The configuration
# cell_size = 28
cols = 10
rows = 22
cell_size = primary_monitor.height / (rows + 2)
maxfps = 120

colors = [
    (0,   0,   0),
    (255, 85,  85),
    (100, 200, 115),
    (120, 108, 245),
    (255, 140, 50),
    (50,  120, 52),
    (146, 202, 73),
    (150, 161, 218),
    (35,  35,  35)  # Helper color for background grid
]

# Define the shapes of the single parts
tetris_shapes = [
    [[1, 1, 1],
     [0, 1, 0]],

    [[0, 2, 2],
     [2, 2, 0]],

    [[3, 3, 0],
     [0, 3, 3]],

    [[4, 0, 0],
     [4, 4, 4]],

    [[0, 0, 5],
     [5, 5, 5]],

    [[6, 6, 6, 6]],

    [[7, 7],
     [7, 7]]
]


def rotate_clockwise(shape):
    return [
        [shape[y][x] for y in range(len(shape))]
        for x in range(len(shape[0]) - 1, -1, -1)
    ]


def check_collision(board, shape, offset):
    off_x, off_y = offset
    for cy, row in enumerate(shape):
        for cx, cell in enumerate(row):
            try:
                if cell and board[cy + off_y][cx + off_x]:
                    return True
            except IndexError:
                return True
    return False


def remove_row(board, row):
    del board[row]
    return [[0 for i in range(cols)]] + board


def join_matrixes(mat1, mat2, mat2_off):
    off_x, off_y = mat2_off
    for cy, row in enumerate(mat2):
        for cx, val in enumerate(row):
            mat1[cy+off_y-1][cx+off_x] += val
    return mat1


def new_board():
    board = [
        [0 for x in range(cols)]
        for y in range(rows)
    ]
    board += [[1 for x in range(cols)]]
    return board


class TetrisApp(object):
    def __init__(self):
        pygame.init()
        pygame.key.set_repeat(250, 25)
        self.width = primary_monitor.width
        self.height = cell_size*(rows+2)
        self.rlim = self.width / 2
        self.llim = self.rlim - cell_size*cols
        self.bground_grid = [[8 if x % 2 == y % 2 else 0 for x in range(cols)] for y in range(rows)]

        font_name = ("C:\\Windows\\Fonts\\arialbd.ttf" if os.name == "nt" else "/usr/share/fonts/truetype/msttcorefonts/Arial_Bold.ttf")
        self.default_font = pygame.font.Font(
            font_name, 22)

        self.screen = pygame.display.set_mode((self.width, self.height), pygame.FULLSCREEN)
        pygame.event.set_blocked(pygame.MOUSEMOTION)
        self.next_stone = tetris_shapes[rand(len(tetris_shapes))]
        self.mouse_enter_pos = None
        self.mouse_leave_pos = None
        self.event_time = None
        self.event_time_start = None
        self.init_game()

    def new_stone(self):
        self.stone = self.next_stone[:]
        self.next_stone = tetris_shapes[rand(len(tetris_shapes))]
        self.stone_x = int(cols / 2 - len(self.stone[0])/2)
        self.stone_y = 0

        if check_collision(self.board,
                           self.stone,
                           (self.stone_x, self.stone_y)):
            self.gameover = True

    def init_game(self):
        self.board = new_board()
        self.new_stone()
        self.level = 1
        self.score = 0
        self.lines = 0
        pygame.time.set_timer(pygame.USEREVENT+1, 1000)

    def disp_msg(self, msg, topleft, text_color=(255, 255, 255), bg_color=(0, 0, 0)):
        x, y = topleft
        for line in msg.splitlines():
            self.screen.blit(
                self.default_font.render(
                    line,
                    False,
                    text_color,
                    bg_color),
                (x, y))
            y += 14

    def center_msg(self, msg):
        for i, line in enumerate(msg.splitlines()):
            msg_image = self.default_font.render(line, False,
                                                 (255, 255, 255), (0, 0, 0))

            msgim_center_x, msgim_center_y = msg_image.get_size()
            msgim_center_x //= 2
            msgim_center_y //= 2

            self.screen.blit(msg_image, (
                self.width // 2-msgim_center_x,
                self.height // 2-msgim_center_y+i*22))

    def draw_matrix(self, matrix, offset):
        off_x, off_y = offset
        off_x = off_x + self.llim / cell_size
        off_y = off_y + 1
        for y, row in enumerate(matrix):
            for x, val in enumerate(row):
                if val:
                    pygame.draw.rect(
                        self.screen,
                        colors[val if y < rows else 0],
                        pygame.Rect(
                            (off_x+x) * cell_size,
                            (off_y+y) * cell_size,
                            cell_size,
                            cell_size),
                        0
                    )
                    pygame.draw.rect(
                        self.screen,
                        colors[-1 if y < rows else 0],
                        pygame.Rect(
                            (off_x+x) * cell_size,
                            (off_y+y) * cell_size,
                            cell_size,
                            cell_size),
                        2
                    )

    def add_cl_lines(self, n):
        linescores = [0, 40, 100, 300, 1200]
        self.lines += n
        self.score += linescores[n] * self.level
        if self.lines >= self.level*6:
            self.level += 1
            newdelay = 1000-50*(self.level-1)
            newdelay = 100 if newdelay < 100 else newdelay
            pygame.time.set_timer(pygame.USEREVENT+1, newdelay)

    def move(self, delta_x):
        if not self.gameover and not self.paused:
            new_x = self.stone_x + delta_x
            if new_x < 0:
                new_x = 0
            if new_x > cols - len(self.stone[0]):
                new_x = cols - len(self.stone[0])
            if not check_collision(self.board,
                                   self.stone,
                                   (new_x, self.stone_y)):
                self.stone_x = new_x

    def quit(self):
        self.screen.fill((0, 0, 0))
        self.center_msg("Exiting...")
        pygame.display.update()
        sys.exit()

    def drop(self, manual):
        if not self.gameover and not self.paused:
            self.score += 1 if manual else 0
            self.stone_y += 1
            if check_collision(self.board,
                               self.stone,
                               (self.stone_x, self.stone_y)):
                self.board = join_matrixes(
                    self.board,
                    self.stone,
                    (self.stone_x, self.stone_y))
                self.new_stone()
                cleared_rows = 0
                while True:
                    for i, row in enumerate(self.board[:-1]):
                        if 0 not in row:
                            self.board = remove_row(
                                self.board, i)
                            cleared_rows += 1
                            break
                    else:
                        break
                self.add_cl_lines(cleared_rows)
                return True
        return False

    def insta_drop(self):
        if not self.gameover and not self.paused:
            while (not self.drop(True)):
                pass

    def rotate_stone(self):
        if not self.gameover and not self.paused:
            new_stone = rotate_clockwise(self.stone)
            if not check_collision(self.board,
                                   new_stone,
                                   (self.stone_x, self.stone_y)):
                self.stone = new_stone

    def toggle_pause(self):
        self.paused = not self.paused

    def start_game(self):
        if self.gameover:
            self.init_game()
            self.gameover = False

    def run(self):
        key_actions = {
            'ESCAPE':   self.quit,
            'LEFT': lambda: self.move(-1),
            'RIGHT': lambda: self.move(+1),
            'DOWN': lambda: self.drop(True),
            'UP':       self.rotate_stone,
            'p':        self.toggle_pause,
            'SPACE':    self.start_game,
            'RETURN':   self.insta_drop
        }

        self.gameover = False
        self.paused = False

        dont_burn_my_cpu = pygame.time.Clock()
        seconds_left = [3, 2, 1, 0]
        while 1:
            self.screen.fill((0, 0, 0))
            if self.gameover:
                self.center_msg("""Game Over!\n\nYour score: %d""" % self.score)
                continue_button = pygame.Rect(self.width-cell_size*23.3, cell_size*(rows*0.62), cell_size*4, cell_size*2)
                pygame.draw.rect(self.screen, (35,  35,  35), continue_button, 0, 20)                                        
                pygame.draw.rect(self.screen, (255,  255,  255), continue_button, 1, 20)
                if self.event_time_start is None and continue_button.collidepoint(pygame.mouse.get_pos()):
                    self.event_time_start = pygame.time.get_ticks()
                elif self.event_time_start is not None and not continue_button.collidepoint(pygame.mouse.get_pos()) and not exit_button.collidepoint(pygame.mouse.get_pos()):
                    self.event_time_start = None
                    self.event_time = None
                if self.event_time_start is not None and continue_button.collidepoint(pygame.mouse.get_pos()):
                    self.event_time = int((pygame.time.get_ticks() - self.event_time_start) / 1000)
                    if self.event_time > 3:
                        self.event_time_start = None
                        self.event_time = None
                        self.start_game()
                        
                if self.event_time is not None and continue_button.collidepoint(pygame.mouse.get_pos()):
                    self.disp_msg("Continuing in:", (self.width-cell_size*22.8, cell_size*(rows*0.64)), bg_color=(35,  35,  35))
                    self.disp_msg("%d" % (seconds_left[self.event_time]), (self.width-cell_size*21.4, cell_size*(rows*0.67)), text_color=colors[1], bg_color=(35,  35,  35))
                else:
                    self.disp_msg("Continue", (self.width-cell_size*22.3, cell_size*(rows*0.65)), bg_color=(35,  35,  35))
            else:
                if self.paused:
                    self.center_msg("Paused")
                    unpause_button = pygame.Rect(self.width-cell_size*23.3, cell_size*(rows*0.6), cell_size*4, cell_size*2)
                    pygame.draw.rect(self.screen, (35,  35,  35), unpause_button, 0, 20)                                        
                    pygame.draw.rect(self.screen, (255,  255,  255), unpause_button, 1, 20)
                    if self.event_time_start is None and unpause_button.collidepoint(pygame.mouse.get_pos()):
                        self.event_time_start = pygame.time.get_ticks()
                    elif self.event_time_start is not None and not unpause_button.collidepoint(pygame.mouse.get_pos()) and not exit_button.collidepoint(pygame.mouse.get_pos()):
                        self.event_time_start = None
                        self.event_time = None
                    if self.event_time_start is not None and unpause_button.collidepoint(pygame.mouse.get_pos()):
                        self.event_time = int((pygame.time.get_ticks() - self.event_time_start) / 1000)
                        if self.event_time > 3:
                            self.event_time_start = None
                            self.event_time = None
                            self.toggle_pause()
                    
                    if self.event_time is not None and unpause_button.collidepoint(pygame.mouse.get_pos()):
                        self.disp_msg("Unpausing in:", (self.width-cell_size*22.8, cell_size*(rows*0.62)), bg_color=(35,  35,  35))
                        self.disp_msg("%d" % (seconds_left[self.event_time]), (self.width-cell_size*21.4, cell_size*(rows*0.65)), text_color=colors[1], bg_color=(35,  35,  35))
                    else:
                        self.disp_msg("Unpause", (self.width-cell_size*22.3, cell_size*(rows*0.63)), bg_color=(35,  35,  35))
                else:
                    self.disp_msg("\nNext:", (self.rlim+cell_size, cell_size))
                    self.disp_msg("Score: %d\n\n\nLevel: %d\n\n\nLines: %d" % (self.score, self.level, self.lines), (self.rlim+cell_size, cell_size*6))
                            
                    pygame.draw.rect(self.screen,
                                     (35,  35,  35),
                                     (self.rlim+cell_size,
                                      cell_size*10,
                                      cell_size*6,
                                      cell_size*6), 0, 20)                                        
                    pygame.draw.rect(self.screen,
                                     (255,  255,  255),
                                     (self.rlim+cell_size,
                                      cell_size*10,
                                      cell_size*6,
                                      cell_size*6), 1, 20)
                    self.draw_matrix(self.bground_grid, (0, 0))
                    self.draw_matrix(self.board, (0, 0))
                    self.draw_matrix(self.stone, (self.stone_x, self.stone_y))
                    self.draw_matrix(self.next_stone, (cols+1, 2))
                    pygame.draw.rect(self.screen,
                                     (255, 255, 255),
                                     (self.llim-1,
                                      cell_size-1,
                                      cell_size*cols+2,
                                      cell_size*rows+2), 1)
                    pause_button = pygame.Rect(self.rlim+cell_size*3, cell_size*(rows - 4), cell_size*4, cell_size*2)
                    exit_button = pygame.Rect(self.rlim+cell_size*3, cell_size*(rows - 1), cell_size*4, cell_size*2)
                    pygame.draw.rect(self.screen, (35,  35,  35), pause_button, 0, 20)                                        
                    pygame.draw.rect(self.screen, (255,  255,  255), pause_button, 1, 20)
                    pygame.draw.rect(self.screen, (35,  35,  35), exit_button, 0, 20)                                        
                    pygame.draw.rect(self.screen, (255,  255,  255), exit_button, 1, 20)
                    
                    if self.event_time_start is None and pause_button.collidepoint(pygame.mouse.get_pos()):
                        self.event_time_start = pygame.time.get_ticks()
                    elif self.event_time_start is not None and not pause_button.collidepoint(pygame.mouse.get_pos()) and not exit_button.collidepoint(pygame.mouse.get_pos()):
                        self.event_time_start = None
                        self.event_time = None
                    if self.event_time_start is not None and pause_button.collidepoint(pygame.mouse.get_pos()):
                        self.event_time = int((pygame.time.get_ticks() - self.event_time_start) / 1000)
                        if self.event_time > 3:
                            self.event_time_start = None
                            self.event_time = None
                            self.toggle_pause()
                    
                    if self.event_time_start is None and exit_button.collidepoint(pygame.mouse.get_pos()):
                        self.event_time_start = pygame.time.get_ticks()
                    elif self.event_time_start is not None and not exit_button.collidepoint(pygame.mouse.get_pos()) and not pause_button.collidepoint(pygame.mouse.get_pos()):
                        self.event_time_start = None
                        self.event_time = None
                    if self.event_time_start is not None and exit_button.collidepoint(pygame.mouse.get_pos()):
                        self.event_time = int((pygame.time.get_ticks() - self.event_time_start) / 1000)
                        if self.event_time > 3:
                            self.event_time_start = None
                            self.event_time = None
                            self.quit()
                    
                    if self.event_time is not None and pause_button.collidepoint(pygame.mouse.get_pos()):
                        self.disp_msg("Pausing in:", (self.rlim+cell_size*3.8, cell_size*(rows - 3.5)), bg_color=(35,  35,  35))
                        self.disp_msg("%d" % (seconds_left[self.event_time]), (self.rlim+cell_size*4.9, cell_size*(rows - 2.9)), text_color=colors[1], bg_color=(35,  35,  35))
                    else:
                        self.disp_msg("Pause", (self.rlim+cell_size*4.3, cell_size*(rows - 3.3)), bg_color=(35,  35,  35))
                    
                    if self.event_time is not None and exit_button.collidepoint(pygame.mouse.get_pos()):
                        self.disp_msg("Exiting in:", (self.rlim+cell_size*3.9, cell_size*(rows - 0.5)), bg_color=(35,  35,  35))
                        self.disp_msg("%d" % (seconds_left[self.event_time]), (self.rlim+cell_size*4.9, cell_size*(rows + 0.1)), text_color=colors[1], bg_color=(35,  35,  35))
                    else:
                        self.disp_msg("Exit", (self.rlim+cell_size*4.5, cell_size*(rows - 0.4)), bg_color=(35,  35,  35))
            
            pygame.mouse.set_visible(False)        
            pygame.draw.circle(self.screen, (255, 0, 255), pygame.mouse.get_pos(), cell_size/1.5, 2)
            pygame.draw.circle(self.screen, (255, 0, 255), pygame.mouse.get_pos(), 4)
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.USEREVENT+1:
                    self.drop(False)
                elif event.type == pygame.QUIT:
                    self.quit()
                elif event.type == pygame.KEYDOWN:
                    for key in key_actions:
                        if event.key == eval("pygame.K_" + key):
                            key_actions[key]()
            
            swipe_area = pygame.Rect(self.rlim+cell_size, cell_size*10, cell_size*6, cell_size*6)
            mouse_pos = pygame.mouse.get_pos()
            
            if self.mouse_enter_pos is None and swipe_area.collidepoint(mouse_pos):
                self.mouse_enter_pos = mouse_pos
            elif self.mouse_leave_pos is None and self.mouse_enter_pos is not None and not swipe_area.collidepoint(mouse_pos):
                self.mouse_leave_pos = mouse_pos
            if self.mouse_enter_pos is not None and self.mouse_leave_pos is not None:
                if self.mouse_enter_pos[0] - self.mouse_leave_pos[0] > cell_size*5:
                    self.move(-1)
                    self.mouse_enter_pos = None
                    self.mouse_leave_pos = None
                elif self.mouse_enter_pos[0] - self.mouse_leave_pos[0] < -cell_size*5:
                    self.move(+1)
                    self.mouse_enter_pos = None
                    self.mouse_leave_pos = None
                elif self.mouse_enter_pos[1] - self.mouse_leave_pos[1] > cell_size*5:
                    self.rotate_stone()
                    self.mouse_enter_pos = None
                    self.mouse_leave_pos = None
                elif self.mouse_enter_pos[1] - self.mouse_leave_pos[1] < -cell_size*5:
                    self.insta_drop()
                    self.mouse_enter_pos = None
                    self.mouse_leave_pos = None
                else:
                    self.mouse_enter_pos = None
                    self.mouse_leave_pos = None
            
            dont_burn_my_cpu.tick(maxfps)


if __name__ == '__main__':
    App = TetrisApp()
    App.run()
