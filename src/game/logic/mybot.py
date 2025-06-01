from typing import Optional, Tuple, Dict, List

from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position, Base
from ..util import get_direction, position_equals


class MyBot(BaseLogic):
    def __init__(self):
        self.goal_position: Optional[Position] = None
        self.teleporters: Dict[str, GameObject] = {}
        self.target_after_teleport: Optional[Position] = None

    # Method Pembantu
    def get_diamonds(self, board: Board) -> List[GameObject]:
        # Mengambil daftar diamond biru dan merah dari papan permainan.
        return [d for d in board.game_objects if d.type == "DiamondGameObject"]

    def get_teleporters(self, board: Board) -> List[GameObject]:
        # Mengambil daftar teleporter dari papan permainan.
        return [d for d in board.game_objects if d.type == "TeleportGameObject"]

    def get_reset_button(self, board: Board) -> GameObject:
        # Mengambil tombol reset dari papan permainan.
        return [d for d in board.game_objects if d.type == "DiamondButtonGameObject"]

    def get_distance_without_teleport(self, pos1: Position, pos2: Position) -> int:
        # Menghitung jarak Manhattan antara dua posisi tanpa mempertimbangkan teleporter
        return abs(pos1.x - pos2.x) + abs(pos1.y - pos2.y)

    def get_distance_with_teleport(self, pos1: Position, pos2: Position, board: Board) -> int:
        # Menghitung jarak antara dua posisi dengan mempertimbangkan teleporter
        direct_distance = self.get_distance_without_teleport(pos1, pos2)

        # Jika tidak ada teleport, langsung return jarak tanpa teleport
        if not self.teleporters:
            return direct_distance

        # Inisialisasi jarak terbaik dengan jarak langsung
        best_distance = direct_distance

        # Evaluasi semua pasangan teleporter
        for pair in self.teleporters.values():
            if len(pair) != 2:
                continue  # pasangan tidak lengkap

            tele1, tele2 = pair

            # Kasus: masuk tele1, keluar di tele2
            to_tele1 = self.get_distance_without_teleport(pos1, tele1.position)
            from_tele2 = self.get_distance_without_teleport(tele2.position, pos2)
            total1 = to_tele1 + 1 + from_tele2  # "+1" adalah aksi teleport

            # Kasus: masuk tele2, keluar di tele1
            to_tele2 = self.get_distance_without_teleport(pos1, tele2.position)
            from_tele1 = self.get_distance_without_teleport(tele1.position, pos2)
            total2 = to_tele2 + 1 + from_tele1

            # Bandingkan dan simpan jarak terbaik
            best_distance = min(best_distance,total1, total2)

        return best_distance

    def is_position_equals(self, pos1: Position, pos2: Position) -> bool:
        if pos1 is None or pos2 is None:
            return False

        return pos1.x == pos2.x and pos1.y == pos2.y
    # Akhir dari Inisialisasi Method Pembantu

    def next_move(self, board_bot: GameObject, board: Board) -> Tuple[int, int]:
        props = board_bot.properties
        current_position = board_bot.position
        base = board_bot.properties.base

        # Fungsi Solusi
        if props.diamonds == 5:
            # Hitung jarak ke base langsung dan via teleport
            jarak_langsung = self.get_distance_without_teleport(current_position, base)
            jarak_teleport = self.get_distance_with_teleport(current_position, base, board)
            if jarak_teleport < jarak_langsung:
                # Temukan teleporter terdekat untuk digunakan
                min_distance = float('inf')
                best_tele = None
                for pair in self.teleporters.values():
                    if len(pair) == 2:
                        for tele in pair:
                            distance = self.get_distance_without_teleport(current_position, tele.position)
                            if distance < min_distance:
                                min_distance = distance
                                best_tele = tele
                if best_tele:
                    self.goal_position = best_tele.position
                else:
                    self.goal_position = base
            else:
                self.goal_position = base
        else:
            if self.target_after_teleport:
                if self.is_position_equals(current_position, self.goal_position):
                    # Sudah sampai di teleporter, sekarang arahkan ke tujuan akhir
                    self.goal_position = self.target_after_teleport
                    self.target_after_teleport = None

            # Inisialisasi Himpunan Kandidat
            diamonds = board.diamonds
            teleporters = self.get_teleporters(board)
            reset_button = self.get_reset_button(board)
            bots = board.bots

            self.teleporters = {}
            for tele in teleporters:
                pair_id = tele.properties.pair_id
                if pair_id not in self.teleporters:
                    self.teleporters[pair_id] = []
                self.teleporters[pair_id].append(tele)

            # Hitung Jarak tanpa Teleporter dan Dengan Teleporter Setiap kandidat
            candidates = []

            for diamond in diamonds:
                distance = self.get_distance_with_teleport(current_position, diamond.position, board)
                candidates.append((diamond, distance))
            for button in reset_button:
                distance = self.get_distance_with_teleport(current_position, button.position, board)
                candidates.append((button, distance))
            for bot in bots:
                distance = self.get_distance_with_teleport(current_position, bot.position, board)
                candidates.append((bot, distance))
            for tele in teleporters:
                distance = self.get_distance_with_teleport(current_position, tele.position, board)
                candidates.append((tele, distance))

            # Fungsi Seleksi
            # Cari Kandidat dengan nilai p/w atau dengan densitas terbaik
            # p = jarak (semakin kecil semakin untung), w = poin
            best_candidate = None
            best_p = -1
            best_w = 100
            best_density = 100
            for candidate, distance in candidates:
                # Fungsi Kelayakan
                if candidate.type == "TeleportGameObject":
                    continue
                if candidate.type == "BotGameObject":
                    continue
                if candidate.type == "DiamondGameObject":
                    # Fungsi Objective
                    # Diamond Biru w = 2, Diamond Merah w = 4, karena perbandingan poin Diamond Biru dan Merah adalah 1/2
                    w = 2 if candidate.properties.points == 1 else 4
                    if props.diamonds + candidate.properties.points > 5:
                        # Jika mengambil akan melebihi kapasitas, maka tidak boleh diambil atau buat nilai p setinggi mungkin
                        p = 1000
                    else:
                        p = distance
                elif candidate.type == "DiamondButtonGameObject":
                    # Tombol Reset w = 1, saya kasih w = 1 karena reset button adalah opsi terakhir jika tidak ada diamond yang bisa diambil / terlalu jauh
                    w = 1
                    p = distance

                density = p / w
                if density < best_density:
                    # Himpunan Solusi
                    best_candidate = candidate
                    best_p = p
                    best_w = w
                    best_density = density

            # Tentukan apakah jarak terbaik melalui teleport
            direct_distance = self.get_distance_without_teleport(current_position, best_candidate.position)
            teleport_distance = self.get_distance_with_teleport(current_position, best_candidate.position, board)

            if teleport_distance < direct_distance:
                # Temukan jalur teleportasi terbaik ke kandidat
                min_total = float('inf')
                for pair in self.teleporters.values():
                    if len(pair) != 2:
                        continue
                    teleport_1, teleport_2 = pair

                    distance_1 = self.get_distance_without_teleport(current_position, teleport_1.position) + \
                        self.get_distance_without_teleport(teleport_2.position, best_candidate.position) + 1

                    distance_2 = self.get_distance_without_teleport(current_position, teleport_2.position) + \
                        self.get_distance_without_teleport(teleport_1.position, best_candidate.position) + 1

                    if distance_1 < min_total:
                        self.goal_position = teleport_1.position
                        self.target_after_teleport = best_candidate.position
                        min_total = distance_1
                    if distance_2 < min_total:
                        self.goal_position = teleport_2.position
                        self.target_after_teleport = best_candidate.position
                        min_total = distance_2
            else:
                self.goal_position = best_candidate.position
                self.target_after_teleport = None

        if self.is_position_equals(current_position, self.goal_position):
            self.goal_position = base

        delta_x, delta_y = get_direction(
            current_position.x,
            current_position.y,
            self.goal_position.x,
            self.goal_position.y,
        )

        return delta_x, delta_y