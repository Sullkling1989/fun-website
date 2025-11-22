import tkinter as tk
import random

class SpaceInvaders:
    def __init__(self, root):
        self.root = root
        self.root.title("Tkinter Space Invaders")

        # Canvas
        self.canvas = tk.Canvas(root, width=600, height=600, bg="black")
        self.canvas.pack()

        # Player
        self.player = self.canvas.create_rectangle(290, 560, 310, 580, fill="white")

        # Variables
        self.bullets = []
        self.invader_bullets = []
        self.invaders = []
        self.barricades = []
        self.score = 0
        self.running = True

        # Score label
        self.score_label = tk.Label(root, text="Score: 0", font=("Arial", 16))
        self.score_label.pack()

        # Controls
        root.bind("<Left>", lambda e: self.move_player(-20))
        root.bind("<Right>", lambda e: self.move_player(20))
        root.bind("<space>", lambda e: self.shoot())
        root.bind("<Return>", lambda e: self.reset_game())

        # Reset / Play Button
        self.reset_button = tk.Button(root, text="Play / Reset", command=self.reset_game)
        self.reset_button.pack(pady=10)

        self.spawn_invaders()
        self.spawn_barricades()
        self.game_loop()

    def move_player(self, dx):
        if self.running:
            self.canvas.move(self.player, dx, 0)

    def shoot(self):
        if self.running:
            x1, y1, x2, y2 = self.canvas.coords(self.player)
            bullet = self.canvas.create_rectangle((x1+x2)//2 - 2, y1 - 10, (x1+x2)//2 + 2, y1, fill="yellow")
            self.bullets.append(bullet)

    def spawn_invaders(self):
        self.invaders.clear()
        for row in range(3):
            for col in range(8):
                x = 50 + col * 60
                y = 50 + row * 40
                inv = self.canvas.create_rectangle(x, y, x+30, y+20, fill="red")
                self.invaders.append(inv)

    def spawn_barricades(self):
        self.barricades.clear()
        for bx in [100, 250, 400]:
            for i in range(5):
                block = self.canvas.create_rectangle(bx + i*10, 480, bx + i*10 + 10, 500, fill="green")
                self.barricades.append(block)

    def move_invaders(self):
        for inv in self.invaders:
            self.canvas.move(inv, 2, 0)

            x1, y1, x2, y2 = self.canvas.coords(inv)
            if x2 >= 600:
                for i in self.invaders:
                    self.canvas.move(i, -200, 20)
                break

        if random.random() < 0.02 and self.invaders:
            shooter = random.choice(self.invaders)
            x1, y1, x2, y2 = self.canvas.coords(shooter)
            bullet = self.canvas.create_rectangle((x1+x2)//2, y2, (x1+x2)//2 + 4, y2+10, fill="orange")
            self.invader_bullets.append(bullet)

    def update_bullets(self):
        # Player bullets
        for bullet in self.bullets[:]:
            self.canvas.move(bullet, 0, -10)
            bx1, by1, bx2, by2 = self.canvas.coords(bullet)

            if by2 < 0:
                self.canvas.delete(bullet)
                self.bullets.remove(bullet)
                continue

            # Hit invader
            for inv in self.invaders[:]:
                ix1, iy1, ix2, iy2 = self.canvas.coords(inv)
                if bx1 < ix2 and bx2 > ix1 and by1 < iy2 and by2 > iy1:
                    self.canvas.delete(inv)
                    self.invaders.remove(inv)
                    self.canvas.delete(bullet)
                    self.bullets.remove(bullet)
                    self.score += 10
                    self.score_label.config(text=f"Score: {self.score}")
                    break

            # Hit barricade
            for block in self.barricades[:]:
                bx1b, by1b, bx2b, by2b = self.canvas.coords(block)
                if bx1 < bx2b and bx2 > bx1b and by1 < by2b and by2 > by1b:
                    self.canvas.delete(block)
                    self.barricades.remove(block)
                    self.canvas.delete(bullet)
                    self.bullets.remove(bullet)
                    break

        # Invader bullets
        for bullet in self.invader_bullets[:]:
            self.canvas.move(bullet, 0, 7)
            bx1, by1, bx2, by2 = self.canvas.coords(bullet)

            if by1 > 600:
                self.canvas.delete(bullet)
                self.invader_bullets.remove(bullet)
                continue

            # Hit player
            px1, py1, px2, py2 = self.canvas.coords(self.player)
            if bx1 < px2 and bx2 > px1 and by1 < py2 and by2 > py1:
                self.running = False
                self.canvas.create_text(300, 300, text="GAME OVER", fill="white", font=("Arial", 30))
                return

            # Hit barricade
            for block in self.barricades[:]:
                bx1b, by1b, bx2b, by2b = self.canvas.coords(block)
                if bx1 < bx2b and bx2 > bx1b and by1 < by2b and by2 > by1b:
                    self.canvas.delete(block)
                    self.barricades.remove(block)
                    self.canvas.delete(bullet)
                    self.invader_bullets.remove(bullet)
                    break

    def check_game_over(self):
        for inv in self.invaders:
            x1, y1, x2, y2 = self.canvas.coords(inv)
            if y2 >= 560:
                self.running = False
                self.canvas.create_text(300, 300, text="GAME OVER", fill="white", font=("Arial", 30))
                return

        if not self.invaders:
            self.running = False
            self.canvas.create_text(300, 300, text="YOU WIN!", fill="white", font=("Arial", 30))

    def game_loop(self):
        if self.running:
            self.move_invaders()
            self.update_bullets()
            self.check_game_over()
        self.root.after(50, self.game_loop)

    def reset_game(self):
        self.running = True
        self.score = 0
        self.score_label.config(text="Score: 0")

        self.canvas.delete("all")

        self.player = self.canvas.create_rectangle(290, 560, 310, 580, fill="white")

        self.bullets.clear()
        self.invader_bullets.clear()
        self.invaders.clear()
        self.barricades.clear()

        self.spawn_invaders()
        self.spawn_barricades()

root = tk.Tk()
game = SpaceInvaders(root)
root.mainloop()