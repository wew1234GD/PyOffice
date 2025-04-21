import pygame
import sys
import json
import tkinter as tk
from tkinter import filedialog
import configparser

config = configparser.ConfigParser()
config.read('config.cfg')

data_size = (config.getint('General', 'WIDHT'), config.getint('General', 'HEIGHT'))
pygame.init()
screen = pygame.display.set_mode(data_size)
pygame.display.set_caption("PyPoint")
clock = pygame.time.Clock()

SIDE_PANEL_W = 100
TOP_PANEL_H = 50
CANVAS_RECT = pygame.Rect(
    SIDE_PANEL_W, TOP_PANEL_H,
    data_size[0] - SIDE_PANEL_W,
    data_size[1] - TOP_PANEL_H
)

COL_BG = (240, 240, 240)
COL_SIDE = (200, 200, 200)
COL_TOP = (180, 180, 180)
COL_BTN = (100, 150, 200)
COL_ACTIVE = (180, 220, 180)
COL_TEXT = (0, 0, 0)
COL_MENU_BG = (220, 220, 220)

side_scroll = 0
SCROLL_STEP = 20

class Button:
    def __init__(self, text, rect, callback):
        self.text = text
        self.rect = pygame.Rect(rect)
        self.callback = callback
        self.font = pygame.font.Font(None, 24)
        self.render()

    def render(self):
        self.image = self.font.render(self.text, True, COL_TEXT)
        self.text_rect = self.image.get_rect(center=self.rect.center)

    def draw(self, surface):
        pygame.draw.rect(surface, COL_BTN, self.rect)
        pygame.draw.rect(surface, COL_TEXT, self.rect, 2)
        surface.blit(self.image, self.text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()

class Menu:
    def __init__(self, options, pos, callbacks):
        self.options = options
        self.callbacks = callbacks
        self.font = pygame.font.Font(None, 24)
        self.pos = pos
        self.items = []
        self.setup()

    def setup(self):
        x, y = self.pos
        h = 30
        for idx, opt in enumerate(self.options):
            rect = pygame.Rect(x, y + idx*h, 120, h)
            surf = self.font.render(opt, True, COL_TEXT)
            self.items.append((opt, rect, surf))

    def draw(self, surface):
        for opt, rect, surf in self.items:
            pygame.draw.rect(surface, COL_MENU_BG, rect)
            pygame.draw.rect(surface, COL_TEXT, rect, 1)
            surface.blit(surf, surf.get_rect(midleft=rect.midleft + pygame.Vector2(5,0)))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for opt, rect, _ in self.items:
                if rect.collidepoint(event.pos):
                    self.callbacks[opt]()
                    return True
        return False

class TextItem:
    def __init__(self, text, font_size, position):
        self.text = text
        self.font_size = font_size
        self.pos = position
        self.dragging = False
        self.selected = False
        self._render()

    def _render(self):
        self.font = pygame.font.Font(None, self.font_size)
        self.image = self.font.render(self.text, True, COL_TEXT)
        self.rect = self.image.get_rect(topleft=self.pos)

    def draw(self, surface):
        surface.blit(self.image, self.rect)
        if self.selected:
            pygame.draw.rect(surface, (0, 120, 215), self.rect, 2)

    def start_drag(self, mouse_pos):
        self.dragging = True
        mx, my = mouse_pos
        self.offset_x = self.rect.x - mx
        self.offset_y = self.rect.y - my

    def update_drag(self, mouse_pos):
        mx, my = mouse_pos
        new_x = mx + self.offset_x
        new_y = my + self.offset_y
        new_x = max(CANVAS_RECT.left, min(new_x, CANVAS_RECT.right - self.rect.width))
        new_y = max(CANVAS_RECT.top, min(new_y, CANVAS_RECT.bottom - self.rect.height))
        self.rect.x = new_x
        self.rect.y = new_y

    def end_drag(self):
        self.dragging = False

    def set_text(self, new_text):
        self.text = new_text
        self._render()

class Slide:
    def __init__(self):
        self.items = []

class SlideManager:
    def __init__(self):
        self.slides = [Slide()]
        self.current = 0

    def add_slide(self):
        self.slides.append(Slide())

    def get_current(self):
        return self.slides[self.current]

    def switch_to(self, idx):
        if 0 <= idx < len(self.slides):
            self.current = idx

    def num_slides(self):
        return len(self.slides)

slide_mgr = SlideManager()
current_font = 32
context_menu = None
presenting = False
present_index = 0

def save_presentation():
    root = tk.Tk(); root.withdraw()
    filename = filedialog.asksaveasfilename(defaultextension='.json',
                                            filetypes=[('JSON Files', '*.json')])
    if not filename:
        return
    data = []
    for slide in slide_mgr.slides:
        slide_data = []
        for item in slide.items:
            slide_data.append({
                'text': item.text,
                'font_size': item.font_size,
                'pos': (item.rect.x, item.rect.y)
            })
        data.append(slide_data)
    with open(filename, 'w') as f:
        json.dump(data, f)

def load_presentation():
    root = tk.Tk(); root.withdraw()
    filename = filedialog.askopenfilename(defaultextension='.json',
                                          filetypes=[('JSON Files', '*.json')])
    if not filename:
        return
    with open(filename, 'r') as f:
        data = json.load(f)
    slide_mgr.slides = []
    for slide_data in data:
        slide = Slide()
        for it in slide_data:
            item = TextItem(it['text'], it['font_size'], it['pos'])
            slide.items.append(item)
        slide_mgr.slides.append(slide)
    slide_mgr.current = 0

def new_slide():
    slide_mgr.add_slide()

def add_text():
    item = TextItem("New text", current_font,
                    (SIDE_PANEL_W + 20, TOP_PANEL_H + 20))
    slide_mgr.get_current().items.append(item)

def increase_font():
    global current_font
    current_font += 4

def decrease_font():
    global current_font
    current_font = max(8, current_font - 4)

def start_presentation():
    global presenting, present_index
    presenting = True
    present_index = 0

buttons = [
    Button("New Slide", (10, 10, 80, 30), new_slide),
    Button("Add Text",  (100, 10, 80, 30), add_text),
    Button("Font +",    (190, 10, 80, 30), increase_font),
    Button("Font -",    (280, 10, 80, 30), decrease_font),
    Button("Present",   (370, 10, 80, 30), start_presentation),
    Button("Save",      (460, 10, 80, 30), save_presentation),
    Button("Load",      (550, 10, 80, 30), load_presentation),
]

def prompt_text(initial=""):
    pygame.key.start_text_input()
    text = initial
    font = pygame.font.Font(None, 32)
    input_rect = pygame.Rect(200, data_size[1]//2 - 20, 400, 40)
    active = True
    while active:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.key.stop_text_input()
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_RETURN:
                    active = False
                elif ev.key == pygame.K_BACKSPACE:
                    text = text[:-1]
                else:
                    text += ev.unicode
        screen.fill(COL_BG)
        pygame.draw.rect(screen, (255,255,255), input_rect)
        img = font.render(text, True, COL_TEXT)
        screen.blit(img, (input_rect.x+5, input_rect.y+5))
        pygame.display.flip(); clock.tick(30)
    pygame.key.stop_text_input()
    return text

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if (event.type == pygame.MOUSEBUTTONDOWN and not presenting
                and event.button in (4, 5)):
            mx, my = event.pos
            if mx < SIDE_PANEL_W and my > TOP_PANEL_H:
                total_h = slide_mgr.num_slides() * 50
                view_h = data_size[1] - TOP_PANEL_H
                max_scroll = min(0, view_h - total_h)
                if event.button == 4:  
                    side_scroll = min(side_scroll + SCROLL_STEP, 0)
                else:                   
                    side_scroll = max(side_scroll - SCROLL_STEP, max_scroll)

        if presenting:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_RIGHT, pygame.K_SPACE):
                    present_index = min(present_index + 1, slide_mgr.num_slides() - 1)
                elif event.key == pygame.K_LEFT:
                    present_index = max(present_index - 1, 0)
                elif event.key == pygame.K_BACKSPACE:
                    presenting = False
            continue

        for btn in buttons:
            btn.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            x, y = event.pos
            if x < SIDE_PANEL_W and y > TOP_PANEL_H:
                idx = (y - TOP_PANEL_H - side_scroll) // 50
                slide_mgr.switch_to(idx)

        if context_menu:
            if context_menu.handle_event(event):
                context_menu = None
            elif event.type == pygame.MOUSEBUTTONDOWN:
                context_menu = None
        else:
            for item in slide_mgr.get_current().items:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                    if item.rect.collidepoint(event.pos):
                        def delete_item(i=item): slide_mgr.get_current().items.remove(i)
                        def edit_item(i=item):  i.set_text(prompt_text(i.text))
                        opts = ["Edit", "Delete"]
                        cbs = {"Edit": edit_item, "Delete": delete_item}
                        context_menu = Menu(opts, event.pos, cbs)
                        break
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if item.rect.collidepoint(event.pos):
                        item.start_drag(event.pos)
                if event.type == pygame.MOUSEMOTION and item.dragging:
                    item.update_drag(event.pos)
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and item.dragging:
                    item.end_drag()

    screen.fill(COL_BG)
    if presenting:
        slide_surf = pygame.Surface((CANVAS_RECT.width, CANVAS_RECT.height))
        slide_surf.fill((255,255,255))
        for item in slide_mgr.slides[present_index].items:
            rel_x = item.rect.x - CANVAS_RECT.left
            rel_y = item.rect.y - CANVAS_RECT.top
            slide_surf.blit(item.image, (rel_x, rel_y))
        scaled = pygame.transform.smoothscale(slide_surf, data_size)
        screen.blit(scaled, (0,0))
    else:
        pygame.draw.rect(screen, COL_TOP, (0, 0, data_size[0], TOP_PANEL_H))
        for btn in buttons:
            btn.draw(screen)

        pygame.draw.rect(screen, COL_SIDE, (0, TOP_PANEL_H, SIDE_PANEL_W, data_size[1] - TOP_PANEL_H))
        clip_rect = pygame.Rect(0, TOP_PANEL_H, SIDE_PANEL_W, data_size[1] - TOP_PANEL_H)
        screen.set_clip(clip_rect)

        for i in range(slide_mgr.num_slides()):
            y0 = TOP_PANEL_H + i*50 + side_scroll
            rect = pygame.Rect(0, y0, SIDE_PANEL_W, 50)
            if rect.bottom < TOP_PANEL_H or rect.top > data_size[1]:
                continue
            col = COL_ACTIVE if i == slide_mgr.current else COL_SIDE
            pygame.draw.rect(screen, col, rect)
            num_surf = pygame.font.Font(None, 36).render(str(i+1), True, COL_TEXT)
            num_rect = num_surf.get_rect()
            num_rect.centerx = SIDE_PANEL_W // 2
            num_rect.centery = y0 + 25
            screen.blit(num_surf, num_rect)

        screen.set_clip(None)

        pygame.draw.rect(screen, (255, 255, 255), CANVAS_RECT)
        for item in slide_mgr.get_current().items:
            item.draw(screen)

        if context_menu:
            context_menu.draw(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()