from typing import List, Tuple, Optional, Dict

from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from game.util import *


class Pesemka(BaseLogic):
    def __init__(self) -> None:
        self.goal: Optional[Position] = None
        self.teleporter_pairs: Dict[str, List[GameObject]] = {}
        self.post_tp_target: Optional[Position] = None

    def _objects_by_type(self, board: Board, type_name: str) -> List[GameObject]:
        return [o for o in board.game_objects if o.type == type_name]

    def _manhattan(self, a: Position, b: Position) -> int:
        return abs(a.x - b.x) + abs(a.y - b.y)

    def _refresh_teleporters(self, board: Board) -> None:
        self.teleporter_pairs.clear()
        for tp in self._objects_by_type(board, "TeleportGameObject"):
            pid = tp.properties.pair_id
            self.teleporter_pairs.setdefault(pid, []).append(tp)

    def _distance_via_tp(self, src: Position, dst: Position) -> int:
        direct = self._manhattan(src, dst)
        if not self.teleporter_pairs:
            return direct

        best = direct
        for pair in self.teleporter_pairs.values():
            if len(pair) != 2:
                continue
            t1, t2 = pair
            # path: src -> t1 -> t2 -> dst
            d1 = self._manhattan(src, t1.position) + 1 + self._manhattan(t2.position, dst)
            # path: src -> t2 -> t1 -> dst
            d2 = self._manhattan(src, t2.position) + 1 + self._manhattan(t1.position, dst)
            best = min(best, d1, d2)
        return best

    def _nearest_tp(self, src: Position) -> Optional[GameObject]:
        if not self.teleporter_pairs:
            return None
        candidate, min_dist = None, float('inf')
        for pair in self.teleporter_pairs.values():
            if len(pair) != 2:
                continue
            for tp in pair:
                dist = self._manhattan(src, tp.position)
                if dist < min_dist:
                    min_dist, candidate = dist, tp
        return candidate

    def _choose_optimal_target(self, bot: GameObject, board: Board) -> Position:
        current = bot.position
        carried = bot.properties.diamonds
        base = bot.properties.base

        # If carrying max diamonds, head home
        if carried >= 5:
            self._refresh_teleporters(board)
            direct_home = self._manhattan(current, base)
            tp_home = self._distance_via_tp(current, base)
            if tp_home < direct_home:
                nearest_tp = self._nearest_tp(current)
                return nearest_tp.position if nearest_tp else base
            return base

        # If in the process of teleporting, and reached teleporter, switch to final target
        if self.post_tp_target and position_equals(current, self.goal):
            target = self.post_tp_target
            self.post_tp_target = None
            return target

        # Build candidate list: (object, distance, weight)
        self._refresh_teleporters(board)
        candidates: List[Tuple[GameObject, int, int]] = []

        # Diamonds: blue=1pt(weight=2), red=2pts(weight=4)
        for diamond in board.diamonds:
            pts = diamond.properties.points
            w = 2 if pts == 1 else 4
            if carried + pts > 5:
                dist = float('inf')
            else:
                dist = self._distance_via_tp(current, diamond.position)
            candidates.append((diamond, dist, w))

        # Reset button: lowest priority weight=1
        for btn in self._objects_by_type(board, "DiamondButtonGameObject"):
            dist = self._distance_via_tp(current, btn.position)
            candidates.append((btn, dist, 1))

        # Score by density = distance / weight
        best_obj, best_density = None, float('inf')
        for obj, dist, w in candidates:
            dens = dist / w if w else float('inf')
            if dens < best_density:
                best_obj, best_density = obj, dens

        if not best_obj:
            return base

        # Decide if teleport path to best_obj is shorter
        direct_dist = self._manhattan(current, best_obj.position)
        tp_dist = self._distance_via_tp(current, best_obj.position)
        if tp_dist < direct_dist:
            # Plan teleport: pick entry teleporter
            chosen_tp, best_route = None, float('inf')
            for pair in self.teleporter_pairs.values():
                if len(pair) != 2:
                    continue
                t1, t2 = pair
                d1 = self._manhattan(current, t1.position) + 1 + self._manhattan(t2.position, best_obj.position)
                d2 = self._manhattan(current, t2.position) + 1 + self._manhattan(t1.position, best_obj.position)
                if d1 < best_route:
                    best_route, chosen_tp = d1, t1
                    self.post_tp_target = best_obj.position
                if d2 < best_route:
                    best_route, chosen_tp = d2, t2
                    self.post_tp_target = best_obj.position
            return chosen_tp.position if chosen_tp else best_obj.position

        return best_obj.position

    def next_move(self, board_bot: GameObject, board: Board) -> Tuple[int, int]:
        self.goal = self._choose_optimal_target(board_bot, board)
        # If already at goal, reset to base
        if position_equals(board_bot.position, self.goal):
            self.goal = board_bot.properties.base

        dx, dy = get_direction(
            board_bot.position.x, board_bot.position.y,
            self.goal.x, self.goal.y
        )
        return dx, dy