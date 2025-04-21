import pygame
import string
import csv
import tkinter as tk
from tkinter import filedialog
import configparser

config = configparser.ConfigParser()
config.read('config.cfg')

pygame.init()
root = tk.Tk()
root.withdraw()

def get_column_label(index):
    label = ''
    while index >= 0:
        label = chr(index % 26 + ord('A')) + label
        index = index // 26 - 1
    return label

WIDTH, HEIGHT = config.getint('General', 'WIDHT'), config.getint('General', 'HEIGHT')
CELL_WIDTH, CELL_HEIGHT = 100, 50
TOOLBAR_HEIGHT = 70
ROWS, COLS = config.getint('excel', 'ROWS'), config.getint('excel', 'COLS')
GRID_Y_OFFSET = TOOLBAR_HEIGHT + CELL_HEIGHT

WHITE         = (255, 255, 255)
GRAY          = (200, 200, 200)
BLACK         = (0, 0, 0)
LIGHT_BLUE    = (173, 216, 230)
BUTTON_COLOR  = (180, 180, 255)
BUTTON_HOVER  = (150, 150, 255)

INPUT_BG      = (220, 220, 220)
INPUT_ACTIVE  = (50, 50, 50)

GREEN         = (0, 200, 0)
RED           = (200, 0, 0)
YELLOW        = (200, 200, 0)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("PyExcel")
font = pygame.font.SysFont(None, 24)

cells = [["" for _ in range(COLS)] for _ in range(ROWS)]
cell_colors = [[WHITE for _ in range(COLS)] for _ in range(ROWS)]
selected_cell = None

offset_x, offset_y = 0, 0
is_panning = False
pan_start = (0, 0)
orig_offset = (0, 0)

input_cols_str = str(COLS)
input_rows_str = str(ROWS)
active_input = None 
input_cols_rect = pygame.Rect(10, 5, 80, 30)
input_rows_rect = pygame.Rect(100, 5, 80, 30)

save_button = pygame.Rect(WIDTH - 100, 20, 90, 30)
load_button = pygame.Rect(WIDTH - 200, 20, 90, 30)
color_buttons = {
    'white':  pygame.Rect(WIDTH - 320, 5, 100, 25),
    'green':  pygame.Rect(WIDTH - 425, 5, 100, 25),
    'red':    pygame.Rect(WIDTH - 320, 35, 100, 25),
    'yellow': pygame.Rect(WIDTH - 425, 35, 100, 25),
}
color_map = {'white': WHITE, 'green': GREEN, 'red': RED, 'yellow': YELLOW}

def save_file():
    path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files","*.csv")])
    if path:
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(cells)

def load_file():
    path = filedialog.askopenfilename(filetypes=[("CSV files","*.csv")])
    if path:
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                if i < ROWS:
                    for j, v in enumerate(row):
                        if j < COLS:
                            cells[i][j] = v

running = True
while running:
    screen.fill(WHITE)

    for col in range(COLS):
        x = CELL_WIDTH + col*CELL_WIDTH + offset_x
        y = TOOLBAR_HEIGHT + offset_y
        label = get_column_label(col)
        text = font.render(label, True, BLACK)
        screen.blit(text, (x + (CELL_WIDTH-text.get_width())//2,
                           y + (CELL_HEIGHT-text.get_height())//2))

    for row in range(ROWS):
        num_txt = font.render(str(row+1), True, BLACK)
        x_num = offset_x + (CELL_WIDTH-num_txt.get_width())//2
        y_num = GRID_Y_OFFSET + row*CELL_HEIGHT + offset_y + (CELL_HEIGHT-num_txt.get_height())//2
        screen.blit(num_txt, (x_num, y_num))
        for col in range(COLS):
            x = CELL_WIDTH + col*CELL_WIDTH + offset_x
            y = GRID_Y_OFFSET + row*CELL_HEIGHT + offset_y
            rect = pygame.Rect(x,y,CELL_WIDTH,CELL_HEIGHT)
            pygame.draw.rect(screen, cell_colors[row][col], rect)
            if selected_cell==(row,col): pygame.draw.rect(screen, LIGHT_BLUE, rect, 3)
            pygame.draw.rect(screen, BLACK, rect, 1)
            ct = font.render(cells[row][col], True, BLACK)
            screen.blit(ct, (x+5,y+5))

    for event in pygame.event.get():
        if event.type==pygame.QUIT:
            running=False
        elif event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
            mx,my=event.pos
            if input_cols_rect.collidepoint(mx,my):
                active_input='cols'
            elif input_rows_rect.collidepoint(mx,my):
                active_input='rows'
            else:
                active_input=None
                if save_button.collidepoint(mx,my): save_file()
                if load_button.collidepoint(mx,my): load_file()
                for nm, r in color_buttons.items():
                    if r.collidepoint(mx,my) and selected_cell:
                        cells[selected_cell[0]][selected_cell[1]] = cells[selected_cell[0]][selected_cell[1]]
                        break
                if mx>CELL_WIDTH+offset_x and my>GRID_Y_OFFSET+offset_y:
                    c = (mx-CELL_WIDTH-offset_x)//CELL_WIDTH
                    r = (my-GRID_Y_OFFSET-offset_y)//CELL_HEIGHT
                    if 0<=r<ROWS and 0<=c<COLS: selected_cell=(r,c)
                    
        elif event.type==pygame.KEYDOWN:
            if active_input in ('cols','rows'):
                s = input_cols_str if active_input=='cols' else input_rows_str
                if event.key==pygame.K_BACKSPACE:
                    s = s[:-1]
                elif event.unicode.isdigit():
                    s += event.unicode
                elif event.key==pygame.K_RETURN and s.isdigit() and int(s)>0:
                    val = int(s)
                    if active_input=='cols': COLS = val
                    else: ROWS = val
                    cells = [["" for _ in range(COLS)] for _ in range(ROWS)]
                    cell_colors = [[WHITE for _ in range(COLS)] for _ in range(ROWS)]
                    offset_x, offset_y = 0,0
                    input_cols_str, input_rows_str = str(COLS), str(ROWS)
                if active_input=='cols': input_cols_str = s
                else: input_rows_str = s
            elif selected_cell and event.type==pygame.KEYDOWN:
                r,c=selected_cell
                if event.key==pygame.K_BACKSPACE:
                    cells[r][c]=cells[r][c][:-1]
                else:
                    cells[r][c]+=event.unicode
        elif event.type==pygame.MOUSEBUTTONDOWN and event.button==3:
            is_panning=True
            pan_start=event.pos
            orig_offset=(offset_x,offset_y)
        elif event.type==pygame.MOUSEBUTTONUP and event.button==3:
            is_panning=False
        elif event.type==pygame.MOUSEMOTION and is_panning:
            dx=event.pos[0]-pan_start[0]
            dy=event.pos[1]-pan_start[1]
            offset_x=orig_offset[0]+dx
            offset_y=orig_offset[1]+dy
            total_w=(COLS+1)*CELL_WIDTH
            total_h=(ROWS+1)*CELL_HEIGHT
            view_w=WIDTH
            view_h=HEIGHT-TOOLBAR_HEIGHT
            min_off_x=min(0,view_w-total_w)
            min_off_y=min(0,view_h-total_h)
            offset_x=max(min_off_x, min(0, offset_x))
            offset_y=max(min_off_y, min(0, offset_y))
    pygame.draw.rect(screen, GRAY, (0,0,WIDTH,TOOLBAR_HEIGHT))

    bg_cols = INPUT_ACTIVE if active_input=='cols' else INPUT_BG
    bg_rows = INPUT_ACTIVE if active_input=='rows' else INPUT_BG
    txt_cols_color = WHITE if active_input=='cols' else BLACK
    txt_rows_color = WHITE if active_input=='rows' else BLACK
    pygame.draw.rect(screen, bg_cols, input_cols_rect)
    pygame.draw.rect(screen, bg_rows, input_rows_rect)
    txt_c = font.render(f"Cols: {input_cols_str}", True, txt_cols_color)
    txt_r = font.render(f"Rows: {input_rows_str}", True, txt_rows_color)
    screen.blit(txt_c, (input_cols_rect.x+5, input_cols_rect.y+5))
    screen.blit(txt_r, (input_rows_rect.x+5, input_rows_rect.y+5))
    
    mouse_pos = pygame.mouse.get_pos()
    for b, label in [(save_button, "Сохранить"), (load_button, "Загрузить")]:
        clr = BUTTON_HOVER if b.collidepoint(mouse_pos) else BUTTON_COLOR
        pygame.draw.rect(screen, clr, b)
        t = font.render(label, True, BLACK)
        screen.blit(t, (b.x+(b.width-t.get_width())//2, b.y+(b.height-t.get_height())//2))
    for name, rect in color_buttons.items():
        pygame.draw.rect(screen, color_map[name], rect)
        pygame.draw.rect(screen, BLACK, rect, 1)
    pygame.display.flip()

pygame.quit()
