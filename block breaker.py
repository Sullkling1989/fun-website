import tkinter as tk
import random
import time

# --- Configurable settings ---
GB_WIDTH = 160    # Game Boy style low resolution width
GB_HEIGHT = 144   # Game Boy style low resolution height
SCALE = 4         # Scale factor for window size (set to 1..8)
WINDOW_W = GB_WIDTH * SCALE
WINDOW_H = GB_HEIGHT * SCALE

PADDLE_W = 28     # in GB pixels
PADDLE_H = 6
PADDLE_Y = GB_HEIGHT - 16
BALL_SIZE = 4     # in GB pixels (square)
BALL_SPEED = 1.6  # base speed in GB pixels per frame
FPS = 60

BRICK_COLS = 8
BRICK_ROWS = 5
BRICK_W = 16
BRICK_H = 8
BRICK_GAP = 2
TOP_MARGIN = 16

LIVES = 5

# Colors — simple "monochrome" GameBoy-like palette (greens)
BG = "#C7F0C7"
FG = "#0B3A0B"
ACCENT = "#4BA84B"
TEXT = FG

# --- Helper conversions ---
def to_screen(x): return int(x * SCALE)
def to_screen_rect(x, y, w, h):
    return (to_screen(x), to_screen(y), to_screen(x + w), to_screen(y + h))

# --- Game class ---
class Breakout:
    def __init__(self, root):
        self.root = root
        root.title("Block Breaker (tkinter)")

        self.canvas = tk.Canvas(root, width=WINDOW_W, height=WINDOW_H, bg=BG, highlightthickness=0)
        self.canvas.pack()
        self.root.resizable(False, False)

        # Bindings
        root.bind("<Left>", lambda e: self.move_paddle(-1))
        root.bind("<Right>", lambda e: self.move_paddle(1))
        root.bind("<KeyRelease-Left>", lambda e: self.move_paddle(0))
        root.bind("<KeyRelease-Right>", lambda e: self.move_paddle(0))
        root.bind("<Return>", lambda e: self.try_restart())
        # also support 'a' and 'd'
        root.bind("a", lambda e: self.move_paddle(-1))
        root.bind("d", lambda e: self.move_paddle(1))
        root.bind("<KeyRelease-a>", lambda e: self.move_paddle(0))
        root.bind("<KeyRelease-d>", lambda e: self.move_paddle(0))

        # Game state
        self.running = True
        self.paused = False
        self.paddle_dx = 0   # -1 left, 1 right, 0 stop
        self.score = 0
        self.high_score = 0

        self.reset_game()
        # Start mainloop timer
        self._last_time = time.time()
        self._tick()

    def reset_game(self):
        # Initialize or reset state variables
        self.paddle_x = (GB_WIDTH - PADDLE_W) // 2
        self.paddle_y = PADDLE_Y
        self.ball_x = GB_WIDTH // 2
        self.ball_y = PADDLE_Y - BALL_SIZE - 1
        angle = random.choice([30, 45, 60, 120, 135, 150])
        rad = angle * 3.14159 / 180.0
        speed = BALL_SPEED
        # randomize horizontal direction
        self.ball_vx = speed * (1 if random.random() < 0.5 else -1) * abs(random.uniform(0.6, 1.0))
        self.ball_vy = -abs(speed * random.uniform(0.6, 1.0))
        self.lives = LIVES
        self.game_over = False
        self.win = False

        self.create_bricks()
        self.draw()

    def create_bricks(self):
        self.bricks = []
        total_width = BRICK_COLS * BRICK_W + (BRICK_COLS - 1) * BRICK_GAP
        start_x = (GB_WIDTH - total_width) // 2
        for row in range(BRICK_ROWS):
            brick_row = []
            for col in range(BRICK_COLS):
                x = start_x + col * (BRICK_W + BRICK_GAP)
                y = TOP_MARGIN + row * (BRICK_H + BRICK_GAP)
                # Each brick: dict with rect and hp (1)
                brick = {"x": x, "y": y, "w": BRICK_W, "h": BRICK_H, "hp": 1}
                brick_row.append(brick)
            self.bricks.append(brick_row)

    def move_paddle(self, direction):
        # direction: -1, 0, 1
        self.paddle_dx = direction

    def try_restart(self):
        if self.game_over or self.win:
            self.reset_game()

    def _tick(self):
        # target FPS loop
        now = time.time()
        dt = now - self._last_time
        self._last_time = now
        if self.running and not self.paused:
            self.update(dt)
            self.draw()
        self.root.after(int(1000 / FPS), self._tick)

    def update(self, dt):
        # Move paddle
        if self.paddle_dx != 0:
            new_x = self.paddle_x + self.paddle_dx * int(100 * dt)  # speed tuned by dt
            # Clamp
            if new_x < 0:
                new_x = 0
            if new_x > GB_WIDTH - PADDLE_W:
                new_x = GB_WIDTH - PADDLE_W
            self.paddle_x = new_x

        if self.game_over or self.win:
            return

        # Move ball with simple physics
        self.ball_x += self.ball_vx * (60 * dt)  # normalized movement to FPS-ish
        self.ball_y += self.ball_vy * (60 * dt)

        # Wall collisions (left/right/top)
        if self.ball_x <= 0:
            self.ball_x = 0
            self.ball_vx = -self.ball_vx
        if self.ball_x + BALL_SIZE >= GB_WIDTH:
            self.ball_x = GB_WIDTH - BALL_SIZE
            self.ball_vx = -self.ball_vx
        if self.ball_y <= 0:
            self.ball_y = 0
            self.ball_vy = -self.ball_vy

        # Paddle collision
        if (self.ball_y + BALL_SIZE >= self.paddle_y and
            self.ball_y + BALL_SIZE <= self.paddle_y + PADDLE_H and
            self.ball_x + BALL_SIZE >= self.paddle_x and
            self.ball_x <= self.paddle_x + PADDLE_W and
            self.ball_vy > 0):
            # reflect with angle depending on hit location
            hit_pos = (self.ball_x + BALL_SIZE/2) - (self.paddle_x + PADDLE_W/2)
            norm = hit_pos / (PADDLE_W/2)
            self.ball_vx += norm * 0.6   # tweak horizontal velocity by hit
            # normalize speed to maintain magnitude
            speed = (self.ball_vx**2 + self.ball_vy**2) ** 0.5
            target_speed = max(BALL_SPEED * 0.9, min(3.5, speed * 0.99))
            # invert vertical
            self.ball_vy = -abs(self.ball_vy)
            # scale to target speed
            cur_speed = (self.ball_vx**2 + self.ball_vy**2) ** 0.5
            if cur_speed != 0:
                scale = target_speed / cur_speed
                self.ball_vx *= scale
                self.ball_vy *= scale

        # Brick collisions — check each brick
        for row in self.bricks:
            for brick in row:
                if brick["hp"] <= 0:
                    continue
                # rectangle collision check
                bx1, by1 = brick["x"], brick["y"]
                bx2, by2 = bx1 + brick["w"], by1 + brick["h"]
                ball_x1, ball_y1 = self.ball_x, self.ball_y
                ball_x2, ball_y2 = ball_x1 + BALL_SIZE, ball_y1 + BALL_SIZE
                if not (ball_x2 < bx1 or ball_x1 > bx2 or ball_y2 < by1 or ball_y1 > by2):
                    # collision occurred — determine side of collision by penetration
                    overlap_left = ball_x2 - bx1
                    overlap_right = bx2 - ball_x1
                    overlap_top = ball_y2 - by1
                    overlap_bottom = by2 - ball_y1
                    min_overlap = min(overlap_left, overlap_right, overlap_top, overlap_bottom)
                    if min_overlap == overlap_left:
                        # hit from left
                        self.ball_x = bx1 - BALL_SIZE
                        self.ball_vx = -abs(self.ball_vx)
                    elif min_overlap == overlap_right:
                        self.ball_x = bx2
                        self.ball_vx = abs(self.ball_vx)
                    elif min_overlap == overlap_top:
                        self.ball_y = by1 - BALL_SIZE
                        self.ball_vy = -abs(self.ball_vy)
                    else:
                        self.ball_y = by2
                        self.ball_vy = abs(self.ball_vy)
                    brick["hp"] -= 1
                    self.score += 10
                    # slight speed-up when hitting a brick
                    self.ball_vx *= 1.02
                    self.ball_vy *= 1.02
                    break  # only one brick collision per update step
            else:
                continue
            break

        # Check lose (ball fell below bottom)
        if self.ball_y > GB_HEIGHT:
            self.lives -= 1
            if self.lives <= 0:
                self.game_over = True
                if self.score > self.high_score:
                    self.high_score = self.score
            else:
                # reset ball on paddle
                self.ball_x = self.paddle_x + PADDLE_W // 2
                self.ball_y = self.paddle_y - BALL_SIZE - 1
                self.ball_vx = BALL_SPEED * (1 if random.random() < 0.5 else -1) * 0.8
                self.ball_vy = -abs(BALL_SPEED * 0.9)

        # Check win (no bricks left)
        bricks_left = sum(1 for row in self.bricks for b in row if b["hp"] > 0)
        if bricks_left == 0:
            self.win = True
            if self.score > self.high_score:
                self.high_score = self.score

    def draw(self):
        self.canvas.delete("all")
        # Background panel (frame)
        pad = to_screen(6)
        self.canvas.create_rectangle(0, 0, WINDOW_W, WINDOW_H, fill=BG, outline=BG)
        self.canvas.create_rectangle(pad, pad, WINDOW_W - pad, WINDOW_H - pad, outline=FG, width=2)

        # Draw bricks
        for row_idx, row in enumerate(self.bricks):
            for col_idx, brick in enumerate(row):
                if brick["hp"] <= 0:
                    continue
                x, y, w, h = brick["x"], brick["y"], brick["w"], brick["h"]
                sx1, sy1, sx2, sy2 = to_screen_rect(x, y, w, h)
                # variant coloring by row
                shade = (row_idx % 3)
                color = ACCENT if shade == 0 else FG if shade == 1 else TEXT
                # draw slightly inset to look retro
                self.canvas.create_rectangle(sx1, sy1, sx2, sy2, outline=FG, fill=color)

        # Draw paddle
        px1, py1, px2, py2 = to_screen_rect(self.paddle_x, self.paddle_y, PADDLE_W, PADDLE_H)
        self.canvas.create_rectangle(px1, py1, px2, py2, fill=FG, outline=FG)

        # Draw ball (as small square)
        bx1, by1, bx2, by2 = to_screen_rect(self.ball_x, self.ball_y, BALL_SIZE, BALL_SIZE)
        self.canvas.create_rectangle(bx1, by1, bx2, by2, fill=TEXT, outline=TEXT)

        # HUD: score and lives
        hud_y = to_screen(4)
        self.canvas.create_text(to_screen(8), hud_y, text=f"Score: {self.score}", anchor="w", fill=TEXT, font=("TkFixedFont", int(6*SCALE)))
        self.canvas.create_text(to_screen(GB_WIDTH-8), hud_y, text=f"Lives: {self.lives}", anchor="e", fill=TEXT, font=("TkFixedFont", int(6*SCALE)))

        # If paused / game over / win show center messages
        if self.game_over or self.win:
            box_w = to_screen(120)
            box_h = to_screen(60)
            cx = WINDOW_W // 2
            cy = WINDOW_H // 2
            self.canvas.create_rectangle(cx - box_w//2, cy - box_h//2, cx + box_w//2, cy + box_h//2, fill=BG, outline=FG, width=2)
            if self.win:
                main = "YOU WIN!"
            else:
                main = "GAME OVER"
            sub = "Press Enter to play again"
            scoreline = f"Score: {self.score}  High: {self.high_score}"
            self.canvas.create_text(cx, cy-12, text=main, fill=FG, font=("TkFixedFont", int(14 * SCALE/3)))
            self.canvas.create_text(cx, cy+6, text=scoreline, fill=TEXT, font=("TkFixedFont", int(8 * SCALE/3)))
            self.canvas.create_text(cx, cy+24, text=sub, fill=FG, font=("TkFixedFont", int(6 * SCALE/3)))
        else:
            # little border/pixel effect
            self.canvas.create_rectangle(to_screen(4), to_screen(4), WINDOW_W-to_screen(4), WINDOW_H-to_screen(4), outline="", width=1)

# --- Run the game ---
if __name__ == "__main__":
    root = tk.Tk()
    game = Breakout(root)

    root.mainloop()
