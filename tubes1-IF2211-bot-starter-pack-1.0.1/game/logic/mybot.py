import heapq
import random
from typing import Optional, List, Tuple, Dict

from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from ..util import position_equals

def get_neighbors(pos: Position, board: Board) -> List[Position]:
    """
    Mengembalikan daftar posisi tetangga valid (atas, bawah, kiri, kanan),
    serta lompatan via teleporter jika pos adalah salah satu teleporter.
    """
    neighbors: List[Position] = []
    deltas = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    for dx, dy in deltas:
        nx, ny = pos.x + dx, pos.y + dy
        if board.is_valid_move(pos, dx, dy):
            neighbors.append(Position(x=nx, y=ny))

    # Teleporter: jika pos berada di teleporter, tambahkan lompat ke teleporter lain
    for obj in board.game_objects:
        if obj.type == "TeleportGameObject" and position_equals(obj.position, pos):
            # cari teleporter lain
            for other in board.game_objects:
                if other.type == "TeleportGameObject" and not position_equals(other.position, pos):
                    neighbors.append(other.position)
            break

    return neighbors

def manhattan(a: Position, b: Position) -> int:
    return abs(a.x - b.x) + abs(a.y - b.y)

def a_star_path(start: Position, goal: Position, board: Board) -> Optional[List[Position]]:
    """
    A* search: mengembalikan jalur terpendek dari start ke goal (termasuk kedua ujung).
    Jika tidak ada jalur, mengembalikan None.
    """
    open_set: List[Tuple[int, Position]] = []
    heapq.heappush(open_set, (manhattan(start, goal), start))

    came_from: Dict[Tuple[int,int], Optional[Tuple[int,int]]] = {}
    g_score: Dict[Tuple[int,int], int] = {}
    start_key = (start.x, start.y)
    came_from[start_key] = None
    g_score[start_key] = 0

    closed: set = set()

    while open_set:
        _, current = heapq.heappop(open_set)
        current_key = (current.x, current.y)

        if position_equals(current, goal):
            # reconstruct path
            path: List[Position] = []
            ck = current_key
            while ck is not None:
                path.append(Position(x=ck[0], y=ck[1]))
                ck = came_from[ck]
            path.reverse()
            return path

        if current_key in closed:
            continue
        closed.add(current_key)

        for nbr in get_neighbors(current, board):
            nbr_key = (nbr.x, nbr.y)
            tentative_g = g_score[current_key] + 1
            if nbr_key in closed and tentative_g >= g_score.get(nbr_key, float('inf')):
                continue

            if tentative_g < g_score.get(nbr_key, float('inf')):
                came_from[nbr_key] = current_key
                g_score[nbr_key] = tentative_g
                f = tentative_g + manhattan(nbr, goal)
                heapq.heappush(open_set, (f, nbr))

    return None

class MyBot(BaseLogic):
    def __init__(self):
        self.current_path: Optional[List[Position]] = None
        self.target_goal: Optional[Position] = None
        self.roam_directions: List[Tuple[int,int]] = [(1,0), (0,1), (-1,0), (0,-1)]
        self.roam_idx: int = 0

    def _find_red_button(self, board: Board) -> Optional[Position]:
        for obj in board.game_objects:
            if obj.type == "DiamondButtonGameObject":
                return obj.position
        return None

    def _nearest_diamond(self, board_bot: GameObject, board: Board) -> Optional[Position]:
        """
        Mencari posisi diamond terdekat (manhattan) tanpa mempertimbangkan cluster,
        lalu kembalikan posisinya.
        """
        if not board.diamonds:
            return None
        current = board_bot.position
        best = board.diamonds[0].position
        best_dist = manhattan(current, best)
        for d in board.diamonds[1:]:
            dist = manhattan(current, d.position)
            if dist < best_dist:
                best = d.position
                best_dist = dist
        return best

    def next_move(self, board_bot: GameObject, board: Board) -> Tuple[int, int]:
        props = board_bot.properties
        pos = board_bot.position
        base = props.base

        # Jika kita sudah mencapai target atau target tidak valid, clear path
        if self.target_goal is not None:
            if position_equals(pos, self.target_goal):
                self.current_path = None
                self.target_goal = None
            else:
                # Jika papan berubah: misal diamond diambil atau red button hilang,
                # cek apakah goal masih relevan (hanya untuk target diamond atau red button).
                # Jika target adalah diamond atau red button, tapi tidak ditemukan lagi, clear path.
                found = False
                for d in board.diamonds:
                    if position_equals(d.position, self.target_goal):
                        found = True
                        break
                if not found:
                    rb = self._find_red_button(board)
                    if self.target_goal != base and (rb is None or not position_equals(rb, self.target_goal)):
                        self.current_path = None
                        self.target_goal = None

        # Tentukan kapan harus kembali ke base: 
        # - inventory penuh
        # - waktu tersisa <= jarak A* ke base + 2 detik buffer
        time_left = props.milliseconds_left // 1000
        need_return = False
        if props.diamonds >= props.inventory_size:
            need_return = True
        else:
            path_to_base = a_star_path(pos, base, board)
            if path_to_base:
                dist_to_base = len(path_to_base) - 1
                if time_left <= dist_to_base + 2:
                    need_return = True
            else:
                # jika tidak ada jalur ke base, tetap roam (meski ini kasus ekstrim)
                need_return = False

        # Jika harus pulang, pastikan target dan path di-set ke base
        if need_return:
            if self.target_goal != base:
                self.target_goal = base
                self.current_path = a_star_path(pos, base, board)
        else:
            # Kita belum perlu pulang → tentukan target:
            # - Jika masih ada red button, ambil red button terlebih dahulu
            # - Jika tidak, ambil diamond terdekat
            red_pos = self._find_red_button(board)
            nearest_diamond = self._nearest_diamond(board_bot, board)

            candidate_goals: List[Position] = []
            if red_pos is not None:
                candidate_goals.append(red_pos)
            if nearest_diamond is not None:
                candidate_goals.append(nearest_diamond)

            # Jika tidak ada target di papan, clear path (roam nanti)
            if not candidate_goals:
                self.current_path = None
                self.target_goal = None
            else:
                # Hitung A* ke tiap kandidat, pilih jalur terpendek
                best_goal = None
                best_path = None
                best_len = float('inf')
                for goal in candidate_goals:
                    path = a_star_path(pos, goal, board)
                    if path:
                        length = len(path) - 1
                        if length < best_len:
                            best_len = length
                            best_goal = goal
                            best_path = path

                if best_goal is not None:
                    # Jika goal baru berbeda dari yang lama, update
                    if not position_equals(best_goal, self.target_goal):
                        self.target_goal = best_goal
                        self.current_path = best_path
                else:
                    # Semua kandidat unreachable: clear path
                    self.current_path = None
                    self.target_goal = None

        # Jika ada path ke target, ambil langkah berikutnya
        if self.current_path and len(self.current_path) >= 2:
            next_pos = self.current_path[1]
            dx = next_pos.x - pos.x
            dy = next_pos.y - pos.y
            return dx, dy

        # Jika tidak ada path (target hilang atau belum ada target), lakukan roaming acak
        for _ in range(len(self.roam_directions)):
            dx, dy = self.roam_directions[self.roam_idx]
            self.roam_idx = (self.roam_idx + 1) % len(self.roam_directions)
            if board.is_valid_move(pos, dx, dy):
                return dx, dy

        # Jika benar-benar tidak bisa bergerak, diam
        return 0, 0
