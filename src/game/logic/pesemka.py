from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from game.util import *


class Pesemka(BaseLogic):
    def __init__(self):
        self.goal = None
        self.teleporter_pairs = {}
        self.post_tp_target = None
        self.position = Position

    def objects_by_type(self, board, type_name):
        return [o for o in board.game_objects if o.type == type_name]

    def grid_distance(self, a, b):
        return abs(a.x - b.x) + abs(a.y - b.y)

    def refresh_teleporters(self, board):
        self.teleporter_pairs.clear()
        for tp in self.objects_by_type(board, "TeleportGameObject"):
            pid = tp.properties.pair_id
            if pid not in self.teleporter_pairs:
                self.teleporter_pairs[pid] = []
            self.teleporter_pairs[pid].append(tp)

    def distance_via_tp(self, src, dst):
        direct = self.grid_distance(src, dst)
        if not self.teleporter_pairs:
            return direct

        best = direct
        for pair in self.teleporter_pairs.values():
            if len(pair) != 2:
                continue
            t1, t2 = pair
            d1 = self.grid_distance(src, t1.position) + 1 + self.grid_distance(t2.position, dst)
            d2 = self.grid_distance(src, t2.position) + 1 + self.grid_distance(t1.position, dst)
            if d1 < best:
                best = d1
            if d2 < best:
                best = d2
        return best

    def nearest_tp(self, src):
        if not self.teleporter_pairs:
            return None
        candidate = None
        min_dist = float('inf')
        for pair in self.teleporter_pairs.values():
            if len(pair) != 2:
                continue
            for tp in pair:
                dist = self.grid_distance(src, tp.position)
                if dist < min_dist:
                    min_dist = dist
                    candidate = tp
        return candidate

    def choose_optimal_target(self, bot, board):
        current = bot.position
        carried = bot.properties.diamonds
        base = bot.properties.base

        # Jika diamond >= 5 maka bot akan pulang
        if carried >= 5:
            self.refresh_teleporters(board)
            direct_home = self.grid_distance(current, base)
            tp_home = self.distance_via_tp(current, base)
            if tp_home < direct_home:
                nearest_tp = self.nearest_tp(current)
                if nearest_tp:
                    return nearest_tp.position
                return base
            return base

        if self.post_tp_target and position_equals(current, self.goal):
            target = self.post_tp_target
            self.post_tp_target = None
            return target

        self.refresh_teleporters(board)
        candidates = []

        for diamond in board.diamonds:
            pts = diamond.properties.points
            w = 2 if pts == 1 else 4
            if carried + pts > 5:
                dist = float('inf')
            else:
                dist = self.distance_via_tp(current, diamond.position)
            candidates.append((diamond, dist, w))

        for btn in self.objects_by_type(board, "DiamondButtonGameObject"):
            dist = self.distance_via_tp(current, btn.position)
            candidates.append((btn, dist, 1))

        # Mengitung density
        best_obj = None
        best_density = float('inf')
        for obj, dist, w in candidates:
            if w == 0:
                dens = float('inf')
            else:
                dens = dist / w
            if dens < best_density:
                best_density = dens
                best_obj = obj

        if not best_obj:
            return base

        direct_dist = self.grid_distance(current, best_obj.position)
        tp_dist = self.distance_via_tp(current, best_obj.position)
        if tp_dist < direct_dist:
            chosen_tp = None
            best_route = float('inf')
            for pair in self.teleporter_pairs.values():
                if len(pair) != 2:
                    continue
                t1, t2 = pair
                d1 = self.grid_distance(current, t1.position) + 1 + self.grid_distance(t2.position, best_obj.position)
                d2 = self.grid_distance(current, t2.position) + 1 + self.grid_distance(t1.position, best_obj.position)
                if d1 < best_route:
                    best_route = d1
                    chosen_tp = t1
                    self.post_tp_target = best_obj.position
                if d2 < best_route:
                    best_route = d2
                    chosen_tp = t2
                    self.post_tp_target = best_obj.position
            if chosen_tp:
                return chosen_tp.position
            return best_obj.position

        return best_obj.position

    def next_move(self, board_bot : GameObject, board : Board):
        self.goal = self.choose_optimal_target(board_bot, board)
        if position_equals(board_bot.position, self.goal):
            self.goal = board_bot.properties.base

        dx, dy = get_direction(
            board_bot.position.x,
            board_bot.position.y,
            self.goal.x,
            self.goal.y
        )
        return dx, dy