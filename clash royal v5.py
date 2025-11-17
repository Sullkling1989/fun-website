"""
clash_tk_v5.py
Clash Royale - style demo (Tkinter) v5

Features:
- 4-card rotating hand (includes spells). Replacement tries to use same elixir cost.
- Enemy bot has its own elixir and 4-card hand, spends only what it has.
- Spells (Arrows, Fireball) can be cast anywhere.
- Crowns counting (1 per regular tower, 3 for king). King ends match.
- Colored turf and deploy borders; deploy area expands when opponent side towers die.
- Giant only attacks towers.
- Friendly-fire fixed (troops/towers only attack opponents).
"""

import tkinter as tk, random, time, math

# ---- Config ----
WIDTH, HEIGHT = 960, 640
FPS = 60

ELIXIR_MAX = 10
ELIXIR_RECHARGE_TIME = 10.0  # seconds for full recharge

# Troop definitions (cost included)
TROOPS = {
    "Knight":       {"speed": 70,  "hp": 80,  "dmg": 10, "range": 18,  "color": "#2E86FF", "cost": 3},
    "Archer":       {"speed": 90,  "hp": 45,  "dmg": 6,  "range": 110, "color": "#FF4081", "cost": 3},
    "Mini P.E.K.K.A.":{"speed":75, "hp": 110, "dmg": 16, "range": 18,  "color": "#7B1FA2", "cost": 4},
    "Giant":        {"speed": 45,  "hp": 220, "dmg": 20, "range": 22,  "color": "#8D6E63", "cost": 5},
    "Musketeer":    {"speed": 70,  "hp": 80,  "dmg": 12, "range": 140, "color": "#03A9F4", "cost": 4},
    "P.E.K.K.A.":   {"speed": 36,  "hp": 260, "dmg": 28, "range": 18,  "color": "#5E35B1", "cost": 7},
}

# Spells
SPELLS = {
    "Arrows":  {"radius": 64,  "damage": 50, "color": "#FFD54F", "cost": 3},
    "Fireball":{"radius": 92,  "damage": 90, "color": "#FF7043", "cost": 4},
}

# Card pool (troops + spells)
ALL_CARDS = list(TROOPS.keys()) + list(SPELLS.keys())

# Towers and scoring
TOWER_HP = 220
KING_HP = 360
TOWER_DMG = 8
KING_DMG = 12
TOWER_RANGE = 110
KING_RANGE = 140

SCORE_TOWER = 1   # crowns
SCORE_KING = 3    # crowns (ends match)

# Layout
LANE_TOP = HEIGHT*0.32
LANE_BOTTOM = HEIGHT*0.68
LANE_CENTER = (LANE_TOP + LANE_BOTTOM)/2

# ---- Entities ----
class Troop:
    def __init__(self, x, y, side, name):
        self.x = float(x); self.y = float(y)
        self.side = side        # "player" or "enemy"
        self.name = name
        d = TROOPS[name]
        self.hp = float(d["hp"])
        self.dmg = float(d["dmg"])
        self.range = float(d["range"])
        self.base_speed = float(d["speed"])
        self.speed = self.base_speed * (1 if side == "player" else -1)
        self.color = d["color"]
        self.alive = True

    def rect(self):
        r = 12
        return (self.x - r, self.y - r, self.x + r, self.y + r)

class Tower:
    def __init__(self, x, y, side, king=False):
        self.x = float(x); self.y = float(y)
        self.side = side
        self.king = king
        self.hp = float(KING_HP if king else TOWER_HP)
        self.dmg = float(KING_DMG if king else TOWER_DMG)
        self.range = float(KING_RANGE if king else TOWER_RANGE)
        self.alive = True

    def rect(self):
        w,h = (28,56) if not self.king else (44,72)
        return (self.x-w/2, self.y-h/2, self.x+w/2, self.y+h/2)

# ---- Utility ----
def now(): return time.time()

def pick_card_with_cost(cost):
    """Return a random card name with exact cost if possible, else +-1 cost choice."""
    exact = [n for n in ALL_CARDS if get_cost(n) == cost]
    if exact:
        return random.choice(exact)
    near = [n for n in ALL_CARDS if abs(get_cost(n) - cost) == 1]
    if near:
        return random.choice(near)
    return random.choice(ALL_CARDS)

def get_cost(name):
    if name in TROOPS: return TROOPS[name]["cost"]
    return SPELLS[name]["cost"]

# ---- Game class ----
class Game:
    def __init__(self, root):
        self.root = root
        root.title("Clash Royale - Tkinter v5")
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="#4FC3F7")
        self.canvas.pack()
        root.resizable(False, False)
        root.bind("<Return>", lambda e: self.try_restart())
        self.canvas.bind("<Button-1>", self.on_click)

        self.reset()
        self._last = now()
        self._tick()

    def reset(self):
        # world
        self.troops = []
        self.towers = []
        self.effects = []   # for spell visuals
        self.selected_card = None
        self.selected_card_idx = None

        # elixir & hands
        self.elixir = ELIXIR_MAX
        self.enemy_elixir = ELIXIR_MAX
        self.elixir_last_pulse = 0
        self.enemy_elixir_last_pulse = 0

        # hands are lists of 4 cards
        self.hand = [random.choice(ALL_CARDS) for _ in range(4)]
        self.enemy_hand = [random.choice(ALL_CARDS) for _ in range(4)]
        # ensure variety: sort doesn't matter

        # crowns
        self.crowns_player = 0
        self.crowns_enemy = 0

        # bot timing & behavior
        self.last_bot_action = now()
        self.bot_delay = 2.2

        # score and game state
        self.score = 0
        self.game_over = False
        self.win = False

        # create towers: left = player, right = enemy
        off = 110
        self.towers = []
        # player: left side (two side towers + king)
        self.towers.append(Tower(110, LANE_CENTER - off/1.5, "player", king=False))
        self.towers.append(Tower(110, LANE_CENTER + off/1.5, "player", king=False))
        self.towers.append(Tower(60, LANE_CENTER, "player", king=True))
        # enemy: right side
        self.towers.append(Tower(WIDTH - 110, LANE_CENTER - off/1.5, "enemy", king=False))
        self.towers.append(Tower(WIDTH - 110, LANE_CENTER + off/1.5, "enemy", king=False))
        self.towers.append(Tower(WIDTH - 60, LANE_CENTER, "enemy", king=True))

    # ----- Input -----
    def on_click(self, e):
        if self.game_over or self.win:
            return
        # click in card bar?
        if e.y > HEIGHT - 120:
            # find card index
            idx = int(e.x // (WIDTH / 4))
            if 0 <= idx < 4:
                # if enough elixir, select
                card = self.hand[idx]
                cost = get_cost(card)
                if self.elixir >= cost:
                    self.selected_card = card
                    self.selected_card_idx = idx
                else:
                    # pulse elixir display
                    self.elixir_last_pulse = now()
        else:
            # attempt to deploy / cast selected card
            if not self.selected_card:
                return
            name = self.selected_card
            cost = get_cost(name)
            if self.elixir < cost:
                self.elixir_last_pulse = now()
                self.selected_card = None; self.selected_card_idx = None
                return

            # Troop placement: must be within player deploy area
            deploy_limit = self.get_player_deploy_limit()
            if name in TROOPS:
                if e.x <= deploy_limit and LANE_TOP <= e.y <= LANE_BOTTOM:
                    # spawn troop
                    self.troops.append(Troop(e.x, e.y, "player", name))
                    self.elixir -= cost
                    self.elixir_last_pulse = now()
                    # replace card in hand with same-cost card if possible
                    self.replace_hand_card(self.selected_card_idx, cost)
                else:
                    # invalid placement pulse
                    self.elixir_last_pulse = now()
            else:
                # Spell: allowed anywhere
                self.cast_spell(e.x, e.y, SPELLS[name], caster="player")
                self.elixir -= cost
                self.elixir_last_pulse = now()
                self.replace_hand_card(self.selected_card_idx, cost)

            self.selected_card = None
            self.selected_card_idx = None

    # ----- Card replacement (hand logic) -----
    def replace_hand_card(self, idx, cost):
        """Replace played card at index idx with a new card of same cost (or +-1 if none)."""
        # try same cost
        same = [c for c in ALL_CARDS if get_cost(c) == cost]
        if same:
            self.hand[idx] = random.choice(same)
            return
        near = [c for c in ALL_CARDS if abs(get_cost(c) - cost) == 1]
        if near:
            self.hand[idx] = random.choice(near)
            return
        # fallback
        self.hand[idx] = random.choice(ALL_CARDS)

    def enemy_replace_hand_card(self, idx, cost):
        same = [c for c in ALL_CARDS if get_cost(c) == cost]
        if same:
            self.enemy_hand[idx] = random.choice(same); return
        near = [c for c in ALL_CARDS if abs(get_cost(c) - cost) == 1]
        if near:
            self.enemy_hand[idx] = random.choice(near); return
        self.enemy_hand[idx] = random.choice(ALL_CARDS)

    # ----- Spells -----
    def cast_spell(self, x, y, spell, caster="player"):
        """Spell hits any units/towers within radius (friendly or enemy). Creates effect."""
        for t in self.troops:
            if math.hypot(t.x - x, t.y - y) <= spell["radius"]:
                t.hp -= spell["damage"]
                if t.hp <= 0:
                    t.alive = False
        for tw in self.towers:
            if math.hypot(tw.x - x, tw.y - y) <= spell["radius"]:
                tw.hp -= spell["damage"]
                if tw.hp <= 0 and tw.alive:
                    tw.alive = False
                    # assign crowns to caster
                    if caster == "player":
                        # if tower is enemy, player gets crown(s)
                        if tw.side == "enemy":
                            if tw.king:
                                self.crowns_player += SCORE_KING
                            else:
                                self.crowns_player += SCORE_TOWER
                    else:
                        if tw.side == "player":
                            if tw.king:
                                self.crowns_enemy += SCORE_KING
                            else:
                                self.crowns_enemy += SCORE_TOWER
        # add effect
        self.effects.append({
            "x": x, "y": y,
            "start": now(), "dur": 0.40,
            "max_r": spell["radius"], "color": spell["color"]
        })

    # ----- Deploy limits (center until side tower destroyed) -----
    def get_player_deploy_limit(self):
        # center by default; expands if enemy side towers are destroyed
        base = WIDTH / 2
        # count enemy side towers (non-king)
        enemy_side_alive = sum(1 for tw in self.towers if tw.side == "enemy" and (not tw.king) and tw.alive)
        destroyed = 2 - enemy_side_alive
        # each destroyed tower extends deploy by 15% of width
        limit = base + destroyed * (WIDTH * 0.15)
        return min(WIDTH * 0.9, limit)

    def get_enemy_deploy_limit(self):
        base = WIDTH / 2
        player_side_alive = sum(1 for tw in self.towers if tw.side == "player" and (not tw.king) and tw.alive)
        destroyed = 2 - player_side_alive
        limit = base - destroyed * (WIDTH * 0.15)
        return max(WIDTH * 0.1, limit)

    # ----- Main update -----
    def update(self, dt):
        if self.game_over or self.win: return

        # elixir regen both sides
        self.elixir = min(ELIXIR_MAX, self.elixir + (ELIXIR_MAX / ELIXIR_RECHARGE_TIME) * dt)
        self.enemy_elixir = min(ELIXIR_MAX, self.enemy_elixir + (ELIXIR_MAX / ELIXIR_RECHARGE_TIME) * dt)

        # Enemy bot: attempt to play from its hand occasionally and only if can afford
        if now() - self.last_bot_action > self.bot_delay:
            self.last_bot_action = now()
            # choose from enemy hand any playable cards
            playable = [ (i,c) for i,c in enumerate(self.enemy_hand) if get_cost(c) <= self.enemy_elixir ]
            if playable:
                idx, card = random.choice(playable)
                cost = get_cost(card)
                self.enemy_elixir -= cost
                # play it: if troop -> spawn on enemy deploy area; if spell -> cast within player's half
                if card in TROOPS:
                    # spawn near right side lane within enemy deploy area
                    e_limit = self.get_enemy_deploy_limit()
                    spawn_x = random.uniform(e_limit + 40, WIDTH - 140)
                    spawn_y = random.choice([LANE_CENTER - 36, LANE_CENTER + 36])
                    self.troops.append(Troop(spawn_x, spawn_y, "enemy", card))
                    # replace in hand with same-cost card
                    self.enemy_replace_hand_card(idx, cost)
                else:
                    # spell cast near player's troops/towers to be meaningful, but anywhere is allowed
                    # pick a target near center-left
                    tx = random.uniform(80, WIDTH * 0.45)
                    ty = random.uniform(LANE_TOP + 20, LANE_BOTTOM - 20)
                    self.cast_spell(tx, ty, SPELLS[card], caster="enemy")
                    self.enemy_replace_hand_card(idx, cost)
            # small randomize bot delay to avoid rigid rhythm
            self.bot_delay = random.uniform(1.8, 3.2)

        # Troop updates and targeting
        for troop in list(self.troops):
            if not troop.alive: continue

            if troop.name == "Giant":
                # Giant: only target towers of opposite side
                targets = [tw for tw in self.towers if tw.alive and tw.side != troop.side]
                target, dmin = None, float("inf")
                for tw in targets:
                    d = abs(tw.x - troop.x)
                    if d < dmin:
                        dmin, target = d, tw
                if target:
                    if dmin <= troop.range:
                        target.hp -= troop.dmg * dt
                        if target.hp <= 0 and target.alive:
                            target.alive = False
                            # award crowns to attacker
                            if troop.side == "player":
                                if target.king:
                                    self.crowns_player += SCORE_KING
                                else:
                                    self.crowns_player += SCORE_TOWER
                            else:
                                if target.king:
                                    self.crowns_enemy += SCORE_KING
                                else:
                                    self.crowns_enemy += SCORE_TOWER
                    else:
                        troop.x += troop.speed * dt
                else:
                    troop.x += troop.speed * dt

            else:
                # normal troop: target nearest enemy troop or tower (opponent only)
                ents = [e for e in self.troops if e.alive and e.side != troop.side]
                towers = [tw for tw in self.towers if tw.alive and tw.side != troop.side]
                candidates = ents + towers
                target, dmin = None, float("inf")
                for e in candidates:
                    ex = e.x if hasattr(e, "x") else e.x
                    d = abs(ex - troop.x)
                    if d < dmin:
                        dmin, target = d, e
                if target:
                    if dmin <= troop.range:
                        target.hp -= troop.dmg * dt
                        if target.hp <= 0:
                            # marking death
                            if isinstance(target, Tower) and target.alive:
                                target.alive = False
                                # award crown to attacker side
                                if troop.side == "player":
                                    if target.king:
                                        self.crowns_player += SCORE_KING
                                    else:
                                        self.crowns_player += SCORE_TOWER
                                else:
                                    if target.king:
                                        self.crowns_enemy += SCORE_KING
                                    else:
                                        self.crowns_enemy += SCORE_TOWER
                            else:
                                target.alive = False
                    else:
                        troop.x += troop.speed * dt
                else:
                    troop.x += troop.speed * dt

            # remove out of bounds
            if troop.x < -40 or troop.x > WIDTH + 40:
                troop.alive = False

        # tidy lists
        self.troops = [t for t in self.troops if t.alive]
        # clean towers list but keep them for crown logic (set alive flag False)
        # towers are kept in list, but alive property used

        # Towers attack enemy troops only
        for tw in self.towers:
            if not tw.alive: continue
            # find closest enemy troop within range
            enemies = [tr for tr in self.troops if tr.alive and tr.side != tw.side]
            for e in enemies:
                if abs(e.x - tw.x) < tw.range and abs(e.y - tw.y) < 80:
                    e.hp -= tw.dmg * dt
                    if e.hp <= 0: e.alive = False
                    break

        # effects expire
        self.effects = [fx for fx in self.effects if now() - fx["start"] < fx["dur"]]

        # Win/Lose: if king dead -> end. Otherwise match continues (we use crown counts only)
        # If king destroyed, assign crowns already above and end match
        player_king_alive = any(tw.side == "player" and tw.king and tw.alive for tw in self.towers)
        enemy_king_alive = any(tw.side == "enemy" and tw.king and tw.alive for tw in self.towers)
        if not enemy_king_alive:
            self.win = True
        if not player_king_alive:
            self.game_over = True

    # ----- DRAW -----
    def draw(self):
        self.canvas.delete("all")
        # background
        self.canvas.create_rectangle(0,0,WIDTH,HEIGHT, fill="#7FC8FF", outline="")

        # draw turf halves: left blue translucent, right red translucent
        self.canvas.create_rectangle(0, LANE_TOP, WIDTH/2, LANE_BOTTOM, fill="#DCEEFF", outline="")
        self.canvas.create_rectangle(WIDTH/2, LANE_TOP, WIDTH, LANE_BOTTOM, fill="#FFE7E7", outline="")

        # draw deploy limits (colored, dashed)
        player_limit = self.get_player_deploy_limit()
        enemy_limit = self.get_enemy_deploy_limit()
        # player area shading
        self.canvas.create_rectangle(0, LANE_TOP, player_limit, LANE_BOTTOM, fill="", outline="#2E86FF", dash=(6,4), width=2)
        # enemy area shading
        self.canvas.create_rectangle(enemy_limit, LANE_TOP, WIDTH, LANE_BOTTOM, fill="", outline="#E53935", dash=(6,4), width=2)

        # draw mid river for clarity
        self.canvas.create_line(WIDTH/2, LANE_TOP, WIDTH/2, LANE_BOTTOM, fill="#888", dash=(4,4))

        # towers
        for tw in self.towers:
            x1,y1,x2,y2 = tw.rect()
            if not tw.alive:
                # draw a destroyed marker (gray)
                self.canvas.create_rectangle(x1,y1,x2,y2, fill="#3a3a3a", outline="")
                continue
            col = "#1565C0" if tw.side == "player'".replace("'", "") else "#D32F2F"  # placeholder to avoid lint
            # select by side correctly:
            col = "#1565C0" if tw.side == "player" else "#D32F2F"
            if tw.king: col = "#0D47A1" if tw.side == "player" else "#B71C1C"
            self.canvas.create_rectangle(x1,y1,x2,y2, fill=col, outline="black")
            # hp bar
            maxhp = KING_HP if tw.king else TOWER_HP
            frac = max(0.0, min(1.0, tw.hp / maxhp))
            bar = 48 if tw.king else 32
            self.canvas.create_rectangle(tw.x - bar/2, y1 - 12, tw.x + bar/2, y1 - 6, fill="#222")
            self.canvas.create_rectangle(tw.x - bar/2, y1 - 12, tw.x - bar/2 + bar * frac, y1 - 6, fill="#76FF03")

        # troops
        for tr in self.troops:
            x1,y1,x2,y2 = tr.rect()
            self.canvas.create_oval(x1,y1,x2,y2, fill=tr.color, outline="black")
            # small label
            lab = tr.name.split()[0]
            self.canvas.create_text(tr.x, tr.y - 18, text=lab, fill="white", font=("Helvetica",8))
            # hp bar
            maxhp = TROOPS[tr.name]["hp"]
            frac = max(0.0, min(1.0, tr.hp / maxhp))
            self.canvas.create_rectangle(tr.x - 12, tr.y - 16, tr.x + 12, tr.y - 12, fill="#222")
            self.canvas.create_rectangle(tr.x - 12, tr.y - 16, tr.x - 12 + 24 * frac, tr.y - 12, fill="#76FF03")

        # spell effects
        for fx in self.effects:
            t = (now() - fx["start"]) / fx["dur"]
            if t > 1.0: continue
            r = t * fx["max_r"]
            self.canvas.create_oval(fx["x"]-r, fx["y"]-r, fx["x"]+r, fx["y"]+r, outline=fx["color"], width=3)

        # draw card bar (bottom) - PLAYER hand (4 cards)
        card_w = WIDTH / 4
        base_y = HEIGHT - 110
        self.canvas.create_rectangle(0, base_y - 8, WIDTH, HEIGHT, fill="#212121", outline="")
        for i, card in enumerate(self.hand):
            x1 = i * card_w + 10
            x2 = (i+1) * card_w - 10
            cost = get_cost(card)
            # card color
            col = TROOPS[card]["color"] if card in TROOPS else SPELLS[card]["color"]
            # grey out if unaffordable
            if self.elixir < cost:
                outline = "#555"
            else:
                outline = "white"
            self.canvas.create_rectangle(x1, base_y + 10, x2, base_y + 100, fill=col, outline=outline, width=3)
            self.canvas.create_text((x1+x2)/2, base_y + 40, text=card, fill="white", font=("Helvetica", 11, "bold"))
            self.canvas.create_text((x1+x2)/2, base_y + 70, text=f"{cost}⛃", fill="#FFEB3B", font=("Helvetica", 12, "bold"))
            # highlight if selected
            if self.selected_card_idx == i:
                self.canvas.create_rectangle(x1-4, base_y+6, x2+4, base_y+104, outline="#FFFF00", width=3)

        # enemy hand display (small icons top-right)
        ehw = 60
        for i, card in enumerate(self.enemy_hand):
            x1 = WIDTH - (i+1)*(ehw+8)
            x2 = x1 + ehw
            col = TROOPS[card]["color"] if card in TROOPS else SPELLS[card]["color"]
            self.canvas.create_rectangle(x1, 12, x2, 12+ehw, fill=col, outline="#222", width=2)
            self.canvas.create_text((x1+x2)/2, 12+ehw/2, text=str(get_cost(card)), fill="white")

        # elixir bars
        def draw_elixir(x,y,frac,label,pulse):
            self.canvas.create_rectangle(x-2,y-2,x+154,y+18, fill="#000")
            self.canvas.create_rectangle(x,y,x+150,y+15, fill="#333")
            self.canvas.create_rectangle(x,y,x+150*frac,y+15, fill="#6A1B9A")
            self.canvas.create_text(x+75, y-10, text=f"{label}: {frac*10:.1f}/10", fill="white", font=("Helvetica",10))
            if pulse and now()-pulse < 0.25:
                self.canvas.create_rectangle(x,y,x+150*frac,y+15, outline="#FFFF00", width=2)
        draw_elixir(14, HEIGHT - 150, self.elixir / ELIXIR_MAX, "Player Elixir", self.elixir_last_pulse)
        draw_elixir(WIDTH - 164, 14, self.enemy_elixir / ELIXIR_MAX, "Enemy Elixir", self.enemy_elixir_last_pulse)

        # crowns / score top center
        # show player crowns (left blue) and enemy crowns (right red)
        cx = WIDTH/2
        self.canvas.create_text(cx, 18, text=f"👑 {self.crowns_player}  -  {self.crowns_enemy} 👑", fill="white", font=("Helvetica", 18, "bold"))

        # show deploy limits text on map
        self.canvas.create_text(player_limit/2, LANE_TOP - 14, text="Your Turf", fill="#1565C0", font=("Helvetica", 10, "bold"))
        self.canvas.create_text((WIDTH + enemy_limit)/2, LANE_TOP - 14, text="Enemy Turf", fill="#D32F2F", font=("Helvetica", 10, "bold"))

        # end messages
        if self.win or self.game_over:
            msg = "YOU WIN!" if self.win else "YOU LOSE!"
            self.canvas.create_rectangle(0,0,WIDTH,HEIGHT, fill="#000000", stipple="gray25")
            self.canvas.create_text(WIDTH/2, HEIGHT/2 - 20, text=msg, fill="#FFEB3B", font=("Helvetica", 36, "bold"))
            self.canvas.create_text(WIDTH/2, HEIGHT/2 + 16, text=f"Player Crowns: {self.crowns_player}   Enemy Crowns: {self.crowns_enemy}", fill="white", font=("Helvetica", 14))
            self.canvas.create_text(WIDTH/2, HEIGHT/2 + 56, text="Press ENTER to restart", fill="white", font=("Helvetica", 12))

    # ---- loop ----
    def _tick(self):
        nowt = now()
        dt = min(0.05, nowt - self._last)
        self._last = nowt
        self.update(dt)
        self.draw()
        self.root.after(int(1000 / FPS), self._tick)

    def try_restart(self):
        if self.win or self.game_over:
            self.reset()

# ---- Run ----
if __name__ == "__main__":
    root = tk.Tk()
    Game(root)
    root.mainloop()
