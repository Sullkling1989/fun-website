


import tkinter as tk
from tkinter import messagebox
import random

class Minesweeper:
    def __init__(self, root, rows=10, cols=10, mines=15):
        self.root = root
        self.rows = rows
        self.cols = cols
        self.mines = mines
        self.buttons = []
        self.mine_positions = set()

        self.create_widgets()
        self.place_mines()

    def create_widgets(self):
        for r in range(self.rows):
            row = []
            for c in range(self.cols):
                btn = tk.Button(self.root, text="", width=3, height=1,
                                command=lambda r=r, c=c: self.reveal_cell(r, c))
                btn.bind("<Button-3>", lambda e, r=r, c=c: self.flag_cell(r, c))
                btn.grid(row=r, column=c)
                row.append(btn)
            self.buttons.append(row)

    def place_mines(self):
        while len(self.mine_positions) < self.mines:
            r = random.randint(0, self.rows - 1)
            c = random.randint(0, self.cols - 1)
            self.mine_positions.add((r, c))

    def reveal_cell(self, r, c):
        if (r, c) in self.mine_positions:
            self.buttons[r][c].config(text="*", bg="red", state="disabled")
            self.game_over()
        else:
            count = self.count_adjacent_mines(r, c)
            self.buttons[r][c].config(text=str(count) if count > 0 else "", state="disabled", relief=tk.SUNKEN)
            if count == 0:
                self.reveal_adjacent_cells(r, c)

    def count_adjacent_mines(self, r, c):
        count = 0
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                nr, nc = r + dr, c + dc
                if (nr, nc) in self.mine_positions:
                    count += 1
        return count

    def reveal_adjacent_cells(self, r, c):
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols and self.buttons[nr][nc]["state"] == "normal":
                    self.reveal_cell(nr, nc)

    def flag_cell(self, r, c):
        btn = self.buttons[r][c]
        if btn["text"] == "F":
            btn.config(text="")
        else:
            btn.config(text="F", fg="blue")

    def game_over(self):
        for r, c in self.mine_positions:
            self.buttons[r][c].config(text="*", bg="red")
        messagebox.showinfo("Game Over", "You clicked on a mine! Game Over.")
        self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Minesweeper")
    game = Minesweeper(root)
    root.mainloop()