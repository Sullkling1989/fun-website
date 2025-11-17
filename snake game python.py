import tkinter as tk
import random

# Constants
WIDTH = 400
HEIGHT = 400
SEG_SIZE = 20
IN_GAME = True

class Snake:
    def __init__(self, canvas):
        self.canvas = canvas
        self.body = [canvas.create_rectangle(SEG_SIZE, SEG_SIZE, SEG_SIZE * 2, SEG_SIZE * 2, fill="green")]
        self.direction = "Right"

    def move(self):
        head_coords = self.canvas.coords(self.body[0])
        x1, y1, x2, y2 = head_coords

        if self.direction == "Right":
            new_coords = (x1 + SEG_SIZE, y1, x2 + SEG_SIZE, y2)
        elif self.direction == "Left":
            new_coords = (x1 - SEG_SIZE, y1, x2 - SEG_SIZE, y2)
        elif self.direction == "Up":
            new_coords = (x1, y1 - SEG_SIZE, x2, y2 - SEG_SIZE)
        elif self.direction == "Down":
            new_coords = (x1, y1 + SEG_SIZE, x2, y2 + SEG_SIZE)

        new_head = self.canvas.create_rectangle(new_coords, fill="green")
        self.body.insert(0, new_head)

        if not self.check_collision():
            tail = self.body.pop()
            self.canvas.delete(tail)

    def change_direction(self, new_direction):
        opposite_directions = {"Right": "Left", "Left": "Right", "Up": "Down", "Down": "Up"}
        if self.direction != opposite_directions[new_direction]:
            self.direction = new_direction

    def check_collision(self):
        global IN_GAME
        head_coords = self.canvas.coords(self.body[0])
        x1, y1, x2, y2 = head_coords

        # Check wall collision
        if x1 < 0 or y1 < 0 or x2 > WIDTH or y2 > HEIGHT:
            IN_GAME = False
            return True

        # Check self collision
        for segment in self.body[1:]:
            if self.canvas.coords(segment) == head_coords:
                IN_GAME = False
                return True

        # Check food collision
        if head_coords == self.canvas.coords(food.food_item):
            return True

        return False


class Food:
    def __init__(self, canvas):
        self.canvas = canvas
        self.food_item = None
        self.place()

    def place(self):
        if self.food_item:
            self.canvas.delete(self.food_item)
        x = random.randint(0, (WIDTH // SEG_SIZE) - 1) * SEG_SIZE
        y = random.randint(0, (HEIGHT // SEG_SIZE) - 1) * SEG_SIZE
        self.food_item = self.canvas.create_rectangle(x, y, x + SEG_SIZE, y + SEG_SIZE, fill="red")


# Game functions
def place_food():
    food.place()

def update_game():
    global IN_GAME
    if IN_GAME:
        if snake.check_collision() and snake.canvas.coords(snake.body[0]) == snake.canvas.coords(food.food_item):
            place_food()
        else:
            snake.move()
        root.after(100, update_game)
    else:
        canvas.create_text(WIDTH / 2, HEIGHT / 2, text="GAME OVER", fill="red", font=("Arial", 24))

def on_key_press(event):
    direction = event.keysym
    if direction in ["Up", "Down", "Left", "Right"]:
        snake.change_direction(direction)


# Main program
root = tk.Tk()
root.title("Snake Game")
canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="black")
canvas.pack()

snake = Snake(canvas)
food = Food(canvas)

root.bind("<KeyPress>", on_key_press)
update_game()

root.mainloop()