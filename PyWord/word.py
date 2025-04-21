import pygame
import sys
import json
import tkinter as tk
from tkinter import filedialog, colorchooser
import configparser
import ast 

Config = configparser.ConfigParser()
Config.read('config.cfg')

root = tk.Tk()
root.withdraw()

pygame.init()

WIN_W, WIN_H = Config.getint('General', 'WIDTH'), Config.getint('General', 'HEIGHT')
CANVAS_W, CANVAS_H = Config.getint('General', 'DOCUMENT_WIDTH'), Config.getint('General', 'DOCUMENT_HEIGHT')
TOOLBAR_HEIGHT = 40


DEFAULT_WINDOW_BG = ast.literal_eval(Config.get('Colors', 'DEFAULT_WINDOW_BG'))
DEFAULT_CANVAS_BG = ast.literal_eval(Config.get('Colors', 'DEFAULT_CANVAS_BG'))
DEFAULT_TEXT_COLOR = ast.literal_eval(Config.get('Colors', 'DEFAULT_TEXT_COLOR'))
CURSOR_COLOR = ast.literal_eval(Config.get('Colors', 'CURSOR_COLOR'))
FPS = Config.getint('General', 'FPS')

FORMAT_BOLD = "bold"
FORMAT_ITALIC = "italic"
FORMAT_UNDERLINE = "underline"
FORMAT_STRIKETHROUGH = "strikethrough"

default_size = 20

ttf_cache = {}
def get_font(size, fmt):
    key = (size, tuple(sorted(fmt)))
    if key in ttf_cache:
        return ttf_cache[key]
    font = pygame.font.SysFont(None, size, bold=(FORMAT_BOLD in fmt), italic=(FORMAT_ITALIC in fmt))
    font.set_underline(FORMAT_UNDERLINE in fmt)
    ttf_cache[key] = font
    return font

class Toolbar:
    def __init__(self, width):
        self.rect = pygame.Rect(0, 0, width, TOOLBAR_HEIGHT)
        self.bold_btn = pygame.Rect(10, 5, 30, 30)
        self.italic_btn = pygame.Rect(50, 5, 30, 30)
        self.underline_btn = pygame.Rect(90, 5, 30, 30)
        self.strike_btn = pygame.Rect(130, 5, 30, 30)
        self.size_up_btn = pygame.Rect(170, 5, 30, 30)
        self.size_down_btn = pygame.Rect(210, 5, 30, 30)
        self.save_btn = pygame.Rect(320, 5, 50, 30)
        self.load_btn = pygame.Rect(380, 5, 50, 30)
        self.color_btn = pygame.Rect(450, 5, 30, 30)

    def draw(self, surf, fmt, size, current_color):
        pygame.draw.rect(surf, (180, 180, 180), self.rect)
        pygame.draw.rect(surf, (150,150,150) if FORMAT_BOLD in fmt else (210,210,210), self.bold_btn)
        surf.blit(get_font(18, {FORMAT_BOLD}).render("Abc", True, current_color), (self.bold_btn.x+3, self.bold_btn.y+7))
        
        pygame.draw.rect(surf, (150,150,150) if FORMAT_ITALIC in fmt else (210,210,210), self.italic_btn)
        surf.blit(get_font(18, {FORMAT_ITALIC}).render("Abc", True, current_color), (self.italic_btn.x+3, self.italic_btn.y+7))
        
        pygame.draw.rect(surf, (150,150,150) if FORMAT_UNDERLINE in fmt else (210,210,210), self.underline_btn)
        surf.blit(get_font(18, {FORMAT_UNDERLINE}).render("Abc", True, current_color), (self.underline_btn.x+3, self.underline_btn.y+7))
        
        pygame.draw.rect(surf, (150,150,150) if FORMAT_STRIKETHROUGH in fmt else (210,210,210), self.strike_btn)
        surf.blit(get_font(18, set()).render("Abc", True, current_color), (self.strike_btn.x+3, self.strike_btn.y+7))
        
        pygame.draw.rect(surf, (210,210,210), self.size_up_btn)
        surf.blit(get_font(18, set()).render("+", True, current_color), (self.size_up_btn.x+8, self.size_up_btn.y+5))
        
        pygame.draw.rect(surf, (210,210,210), self.size_down_btn)
        surf.blit(get_font(18, set()).render("-", True, current_color), (self.size_down_btn.x+10, self.size_down_btn.y+5))
        
        surf.blit(get_font(18, set()).render(f"Size: {size}", True, current_color), (self.size_down_btn.x+40, self.size_down_btn.y+10))
        
        pygame.draw.rect(surf, (150,0,150), self.save_btn)
        surf.blit(get_font(16, set()).render("Save", True, (255,255,255)), (self.save_btn.x+5, self.save_btn.y+7))
        
        pygame.draw.rect(surf, (0,150,200), self.load_btn)
        surf.blit(get_font(16, set()).render("Load", True, (255,255,255)), (self.load_btn.x+5, self.load_btn.y+7))
        
        pygame.draw.rect(surf, current_color, self.color_btn)
        pygame.draw.rect(surf, (0,0,0), self.color_btn, 1)

class TextBox:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.rect = pygame.Rect(x, y, CANVAS_W, CANVAS_H)
        self.lines = [[]]
        self.cursor = [0, 0]
        self.formatting = set()
        self.size = default_size
        self.text_color = DEFAULT_TEXT_COLOR

        self.scroll_offset = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEWHEEL:
            if self.rect.collidepoint(pygame.mouse.get_pos()):
                self.scroll_offset += event.y * self.size
                total_height = len(self.lines) * self.size + 10
                max_offset = 0
                min_offset = min(0, CANVAS_H - total_height)
                self.scroll_offset = max(min(self.scroll_offset, max_offset), min_offset)
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            mx, my = event.pos
            self.set_cursor_by_pos(mx, my)
            return

        if event.type == pygame.KEYDOWN:
            line, idx = self.cursor
            if event.key == pygame.K_RETURN:
                rest = self.lines[line][idx:]
                self.lines[line] = self.lines[line][:idx]
                self.lines.insert(line+1, rest)
                self.cursor = [line+1, 0]
            elif event.key == pygame.K_BACKSPACE:
                if idx > 0:
                    self.lines[line].pop(idx-1)
                    self.cursor[1] -= 1
                elif line > 0:
                    prev_len = len(self.lines[line-1])
                    self.lines[line-1] += self.lines[line]
                    self.lines.pop(line)
                    self.cursor = [line-1, prev_len]
            else:
                ch = event.unicode
                if ch:
                    self.lines[line].insert(idx, (ch, set(self.formatting), self.size, self.text_color))
                    self.cursor[1] += 1

    def set_cursor_by_pos(self, mx, my):
        rel_y = my - (self.y + 5) - self.scroll_offset
        line_index = max(0, min(len(self.lines)-1, rel_y // self.size))
        rel_x = mx - (self.x + 5)
        cum_x = 0
        idx = 0
        for ch, fmt, sz, col in self.lines[line_index]:
            glyph_w, _ = get_font(sz, fmt).size(ch)
            if cum_x + glyph_w/2 >= rel_x:
                break
            cum_x += glyph_w
            idx += 1
        self.cursor = [line_index, idx]

    def draw(self, surf):
        pygame.draw.rect(surf, DEFAULT_CANVAS_BG, self.rect)
        prev_clip = surf.get_clip()
        surf.set_clip(self.rect)

        y = self.y + 5 + self.scroll_offset
        for line in self.lines:
            x = self.x + 5
            for ch, fmt, sz, col in line:
                font = get_font(sz, fmt)
                glyph = font.render(ch, True, col)
                if x + glyph.get_width() > self.x + CANVAS_W - 5:
                    x = self.x + 5
                    y += sz
                surf.blit(glyph, (x, y))
                if FORMAT_STRIKETHROUGH in fmt:
                    pygame.draw.line(surf, col, (x, y+sz//2), (x+glyph.get_width(), y+sz//2), 1)
                x += glyph.get_width()
            y += self.size

        cx, cy = self.get_cursor_pos()
        pygame.draw.rect(surf, CURSOR_COLOR, (cx, cy + self.scroll_offset, 2, self.size))
        surf.set_clip(prev_clip)

    def get_cursor_pos(self):
        line, idx = self.cursor
        y = self.y + 5 + line * self.size
        x = self.x + 5
        for ch, fmt, sz, col in self.lines[line][:idx]:
            x += get_font(sz, fmt).size(ch)[0]
        return x, y

    def save(self, filename=None):
        if not filename:
            filename = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON','*.json')])
        if filename:
            data = {"lines": [[(c, list(f), s, col) for c, ф, s, col in line] for line in self.lines]}
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)

    def load(self, filename=None):
        if not filename:
            filename = filedialog.askopenfilename(filetypes=[('JSON','*.json')])
        if filename:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.lines = [[(c, set(f), s, tuple(col)) for c, f, s, col in line] for line in data.get("lines", [])]
            self.cursor = [0, len(self.lines[0]) if self.lines else 0]
            self.scroll_offset = 0


def main():
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("PyWord")
    clock = pygame.time.Clock()

    canvas_x = (WIN_W - CANVAS_W) // 2
    canvas_y = TOOLBAR_HEIGHT + (WIN_H - TOOLBAR_HEIGHT - CANVAS_H) // 2
    toolbar = Toolbar(WIN_W)
    tb = TextBox(canvas_x, canvas_y)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                if toolbar.bold_btn.collidepoint(pos):
                    tb.formatting ^= {FORMAT_BOLD}
                elif toolbar.italic_btn.collidepoint(pos):
                    tb.formatting ^= {FORMAT_ITALIC}
                elif toolbar.underline_btn.collidepoint(pos):
                    tb.formatting ^= {FORMAT_UNDERLINE}
                elif toolbar.strike_btn.collidepoint(pos):
                    tb.formatting ^= {FORMAT_STRIKETHROUGH}
                elif toolbar.size_up_btn.collidepoint(pos):
                    tb.size += 1
                elif toolbar.size_down_btn.collidepoint(pos) and tb.size > 6:
                    tb.size -= 1
                elif toolbar.save_btn.collidepoint(pos):
                    tb.save()
                elif toolbar.load_btn.collidepoint(pos):
                    tb.load()
                elif toolbar.color_btn.collidepoint(pos):
                    color = colorchooser.askcolor(initialcolor=tb.text_color)[0]
                    if color:
                        tb.text_color = tuple(map(int, color))
                else:
                    tb.handle_event(event)
            elif event.type == pygame.MOUSEWHEEL:
                tb.handle_event(event)
            else:
                tb.handle_event(event)

        screen.fill(DEFAULT_WINDOW_BG)
        toolbar.draw(screen, tb.formatting, tb.size, tb.text_color)
        tb.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()