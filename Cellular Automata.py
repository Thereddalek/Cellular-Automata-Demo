import pygame as pg
import random
from math import floor
import colorsys

W, H = 1000, 1000
CTRL = 700
RES = 500
CW = W // RES
BASE = 3
ALLOWED_STATES = [0, BASE-1]

GRID = False
INITIAL = 0
GREY = 0

KEEP = False

def int_to_base_array(n, base):
    if n == 0:
        return [0]
    
    result = [n % base]
    result[:0] = int_to_base_array(n // base, base)
    
    return result

def base_array_to_int(a: list[int], base) -> int:
    result = 0
    for i, state in enumerate(a):
        result += state * (base ** (len(a)-1-i))

    return result

def hsv_rgb(h, s, v):
    rgbf = colorsys.hsv_to_rgb(h, s, v)
    rgb = [rgbf[0]*255, rgbf[1]*255, rgbf[2]*255]
    return rgb

def generate_colours():
    global COLOURS

    if GREY:
        COLOURS = [255 - int(i / (BASE-1) * 255) for i in range(BASE)]
        for i, C in enumerate(COLOURS):
            COLOURS[i] = (C, C, C)
    else:
        hues = [1.0 - i / (BASE) for i in range(BASE)]
        COLOURS = [hsv_rgb(hues[i], 0.75, 1.0) for i in range(BASE)]

class Cell(pg.Rect):
    def __init__(self, initial_state, x_coord) -> None:
        super().__init__(x_coord, 0, CW, CW)
        self._state = initial_state
        self._buffer_state = initial_state
        self._x_coord = x_coord

    def get_state(self):
        return self._state
    
    def set_state(self, state):
        if state >= ALLOWED_STATES[0] and state <= ALLOWED_STATES[1]:
            self._state = state
        else:
            raise ValueError
        
    def set_buffer(self, state):
        self._buffer_state = state

    def apply_buffer(self):
        self.set_state(self._buffer_state)

    def _move(self, coord: tuple):
        return self.move(coord[0], coord[1])

    def render(self, cnv, t):
        new_rect = self._move((0, t * CW))
        pg.draw.rect(cnv, COLOURS[self.get_state()], new_rect)

    def __repr__(self) -> str:
        return str(self._state) + " " + str(self._x_coord)

class Model:
    def __init__(self, win) -> None:
        self.reset()
        self.win = win

    def reset(self):
        self.T = 0
        if not KEEP:
            self.RULE_INT = random.randint(0, BASE**(BASE**3))
            self.RULE = int_to_base_array(self.RULE_INT, BASE)
            self.RULE = [0] * (BASE**3 - len(self.RULE)) + self.RULE

        self.cnv = pg.Surface((W, H))
        self.cnv.fill((255, 255, 255))

        self.cells = []
        for i in range(RES):
            if INITIAL:
                self.cells.append(Cell(random.randint(0, BASE-1), i*CW))
            else:
                self.cells.append(Cell(0, i*CW))

        if not INITIAL:
            self.cells[floor(len(self.cells)/2)] = Cell(1, CW * floor(len(self.cells)/2))

    def draw_cells(self, cells: list[Cell], cnv, t):
        for cell in cells:
            cell.render(cnv, t)

    def update(self, cells: list[Cell]):
        for i, cell in enumerate(cells):
            if i == len(cells) - 1:
                nhood = [cells[i-1].get_state(), cell.get_state(), cells[0].get_state()]
            else:
                nhood = [cells[i-1].get_state(), cell.get_state(), cells[i+1].get_state()]
            id = base_array_to_int(nhood, BASE)
            new = self.RULE[len(self.RULE) - id - 1]
            cell.set_buffer(new)
        for cell in cells:
            cell.apply_buffer()

    def draw(self):
        while self.T < RES:
            self.draw_cells(self.cells, self.cnv, self.T)
            draw_grid(self.cnv)

            self.win.blit(self.cnv, (0,0))

            self.T += 1
            self.update(self.cells)

            pg.display.flip()

class Ctrl:
    def __init__(self, win) -> None:
        self.win = win

        self.next = Button(W+50, 50, 100, 100, (30, 200, 30), "Next", (0, 100, 0), font_size=40)
        self.initial_conditions = Button(W+450, 50, 200, 100, (30, 200, 30), "Change Initial Conditions", (0, 100, 0), font_size=23)
        self.colour = Button(W+270, 50, 170, 100, (30, 200, 30), "Change Colour Mode", (0, 100, 0), font_size=23)

        self.slider = Slider(W+CTRL//2 - 100, 400, 200, 2, 10, 2)
        self.slider2 = Slider(W+CTRL//2 - 150, 650, 300, 1, W, 100)

        self.up = Button(W+CTRL//2 + 225, 600, 40, 20, (30, 200, 30), "Up", (0, 100, 0), font_size=20)
        self.down = Button(W+CTRL//2 + 225, 650, 40, 20, (30, 200, 30), "Down", (0, 100, 0), font_size=20)

        self.keep_rule = Button(W+160, 50, 100, 100, (30, 200, 30), "Keep Rule", (0, 100, 0), font_size=23, toggle=True)

    def text(self, RULE_INT, RULE: list[int]):
        font = pg.font.Font(None, 20)
        self.RULE_INT = RULE_INT
        self.RULE = RULE

        self.text1 = font.render(f'Base: {BASE}', True, (255, 255, 255))
        self.text1rect = self.text1.get_rect()
        self.text1rect.center = (W+CTRL//2, 350)

        self.text2 = font.render(f'Rule Int: {RULE_INT}', True, (255, 255, 255))
        self.text2rect = self.text2.get_rect()
        self.text2rect.center = (W+CTRL//2, 450)

        self.text3 = font.render(f'Rule Base {BASE}: ' + ''.join(map(str, RULE)), True, (255, 255, 255))
        self.text3rect = self.text3.get_rect()
        self.text3rect.center = (W+CTRL//2, 500)

        self.text4 = font.render("Mode: " + ("Middle" if not INITIAL else "Random"), True, (255, 255, 255))
        self.text4rect = self.text4.get_rect()
        self.text4rect.center = (W+CTRL//2, 200)

        self.text5 = font.render("Mode: " + ("Grey" if GREY else "Colour"), True, (255, 255, 255))
        self.text5rect = self.text5.get_rect()
        self.text5rect.center = (W+CTRL//2, 250)

        self.text6 = font.render(f"Resolution: {RES}", True, (255, 255, 255))
        self.text6rect = self.text6.get_rect()
        self.text6rect.center = (W+CTRL//2, 600)

    def render(self):
        global BASE, ALLOWED_STATES, RES, CW

        self.slider.update()
        self.slider.draw(self.win)

        self.slider2.update()
        self.slider2.draw(self.win)

        BASE = self.slider.get_value()
        ALLOWED_STATES = [0, BASE-1]
        generate_colours()
        self.text(self.RULE_INT, self.RULE)

        RES = self.slider2.get_value()
        CW = W // RES

        self.next.draw(self.win)
        self.initial_conditions.draw(self.win)
        self.colour.draw(self.win)
        self.up.draw(self.win)
        self.down.draw(self.win)
        self.keep_rule.draw(self.win)

        self.win.blit(self.text1, self.text1rect)
        self.win.blit(self.text2, self.text2rect)
        self.win.blit(self.text3, self.text3rect)
        self.win.blit(self.text4, self.text4rect)
        self.win.blit(self.text5, self.text5rect)
        self.win.blit(self.text6, self.text6rect)

        pg.display.update()

class Button:
    def __init__(self, x, y, width, height, color, text, text_color, font_size=20, toggle=False):
        self.rect = pg.Rect(x, y, width, height)
        self.color = color
        self.ambient = self.color
        self.text = text
        self.text_color = text_color
        self.font = pg.font.Font(None, font_size)
        self.toggle = toggle

    def draw(self, screen):
        pg.draw.rect(screen, self.color, self.rect)
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def is_clicked(self, event):
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.color = (0, 70, 0) if self.color == self.ambient else self.ambient
                return True
        
        if not self.toggle:
            self.color = self.ambient
        return False

class Slider:
    def __init__(self, x, y, length, min_value, max_value, initial_value, color=(100, 100, 100), handle_color=(200, 200, 200)):
        self.rect = pg.Rect(x, y, length, 10)
        self.handle_rect = pg.Rect(x + initial_value * (length / (max_value - min_value)) - 10, y - 5, 20, 20)
        self.min_value = min_value
        self.max_value = max_value
        self.value_range = max_value - min_value
        self.value = initial_value
        self.color = color
        self.handle_color = handle_color
        self.dragging = False

    def draw(self, screen):
        pg.draw.rect(screen, self.color, self.rect)
        pg.draw.ellipse(screen, self.handle_color, self.handle_rect)

    def update(self):
        if self.dragging:
            mouse_x, _ = pg.mouse.get_pos()
            mouse_x = max(self.rect.left, min(self.rect.right, mouse_x))
            self.handle_rect.centerx = mouse_x
            self.value = self.min_value + (self.handle_rect.centerx - self.rect.left) / self.rect.width * self.value_range

    def handle_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            if self.handle_rect.collidepoint(event.pos):
                self.dragging = True
        elif event.type == pg.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pg.MOUSEMOTION:
            if self.dragging:
                self.update()

    def get_value(self):
        return round(self.value)

def draw_grid(cnv: pg.Surface):
    if GRID:
        for i in range(RES):
            pg.draw.line(cnv, (50,50,50), (i * CW, 0), (i * CW, H), width=1)
            pg.draw.line(cnv, (50,50,50), (0, i * CW), (W, i * CW), width=1)

def main():
    global INITIAL, GREY, RES, KEEP

    pg.init()
    pg.display.init()
    win = pg.display.set_mode((W+CTRL, H))
    model = Model(win)
    ctrl = Ctrl(win)

    while True:
        pg.draw.rect(win, (0,0,0), pg.Rect(W, 0, CTRL, H))
        ctrl.text(model.RULE_INT, model.RULE)
        ctrl.render()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.display.quit()
                pg.quit()
                exit()
            elif ctrl.next.is_clicked(event):
                ctrl.next.draw(win)
                model.reset()
                model.draw()
            elif ctrl.initial_conditions.is_clicked(event):
                INITIAL = 0 if INITIAL else 1
            elif ctrl.colour.is_clicked(event):
                GREY = 0 if GREY else 1
                generate_colours()
            elif ctrl.up.is_clicked(event):
                RES += 1
                ctrl.slider2.value = RES
            elif ctrl.down.is_clicked(event):
                RES -= 1
                ctrl.slider2.value = RES
            elif ctrl.keep_rule.is_clicked(event):
                KEEP = False if KEEP else True
            ctrl.slider.handle_event(event)
            ctrl.slider2.handle_event(event)

if __name__ == "__main__":
    main()