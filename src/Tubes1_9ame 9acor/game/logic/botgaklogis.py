import random
from game.util import get_direction, position_equals
from game.models import GameObject, Board
from game.logic.base import BaseLogic


class BotGakLogis(BaseLogic):
    def __init__(self):
        super().__init__()
        self.goal_position = None
        self.previous_position = (None, None)
        self.turn_direction = 1
        self.RED_DIAMOND_SCORE_MULTIPLIER = 2.0  # Pengali skor untuk redDiamond
        self.stuck_counter = 0  # Counter untuk mendeteksi stuck
        self.max_stuck_attempts = 3  # Maksimal attempts sebelum random move
        self.tackle_threshold_diamonds = 3  # Jumlah berlian musuh untuk mulai menyerang
        self.targeted_enemy_id = None # ID bot musuh yang sedang ditarget
        self.SCAN_RADIUS = 5  # Jarak pemindaian dalam blok, diperbesar menjadi 5

        # Atribut baru untuk eksplorasi semi-random
        self.exploration_direction = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])

    def next_move(self, board_bot: GameObject, board: Board):
        props = board_bot.properties
        current_position = board_bot.position

        # --- FASE 1: Menentukan Tujuan (Goal Setting) ---

        # PRIORITAS 1: Kembali ke markas jika inventaris penuh
        if props.diamonds >= props.inventory_size:
            self.goal_position = props.base
            self.targeted_enemy_id = None # Reset target
            if position_equals(current_position, self.goal_position):
                self.goal_position = None
        
        # PRIORITAS 2: Kembali ke markas jika waktu sudah menipis (dan punya berlian)
        elif hasattr(board, 'time_left') and board.time_left < 10000 and props.diamonds > 0:
            self.goal_position = props.base
            self.targeted_enemy_id = None # Reset target
            if position_equals(current_position, self.goal_position):
                self.goal_position = None

        # PRIORITAS 3: Cari berlian (berdasarkan skor bobot)
        else:
            best_diamond = self._find_best_diamond_in_radius(current_position, props, board)
            if best_diamond:
                self.goal_position = best_diamond.position
                self.targeted_enemy_id = None # Reset target jika ada diamond
                # Atur ulang arah eksplorasi karena menemukan tujuan
                self.exploration_direction = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
            else:
                # Jika TIDAK ADA diamond dalam radius scan, baru cari bot musuh
                tackle_target = self._find_tackle_target_in_radius(board_bot, board)
                if tackle_target:
                    self.goal_position = tackle_target.position
                    self.targeted_enemy_id = tackle_target.id
                    # Atur ulang arah eksplorasi karena menemukan tujuan
                    self.exploration_direction = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
                else:
                    # Jika tidak ada diamond dan tidak ada bot musuh dalam radius,
                    # atau jika punya diamond tapi tidak ada tujuan lain, kembali ke markas
                    if props.diamonds > 0:
                        self.goal_position = props.base
                        self.targeted_enemy_id = None # Reset target
                        # Atur ulang arah eksplorasi karena menemukan tujuan
                        self.exploration_direction = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
                    else:
                        # Tidak ada tujuan sama sekali, bot akan melakukan semi-random walk
                        self.goal_position = None
                        self.targeted_enemy_id = None

        # --- FASE 2: Pergerakan Menuju Tujuan & Penanganan Terjebak ---
        if self.goal_position:
            return self._move_towards_goal(current_position, board)
        else:
            # Semi-random movement jika tidak ada tujuan
            return self._semi_random_explore(current_position, board)

    def _find_best_diamond_in_radius(self, current_position, props, board):
        """Mencari diamond terbaik berdasarkan skor dalam SCAN_RADIUS"""
        best_score = -1.0
        best_diamond = None
        space_left = props.inventory_size - props.diamonds

        for diamond in board.diamonds:
            # Cek apakah diamond bisa diambil DAN dalam jangkauan scan
            if (diamond.properties.points <= space_left and 
                not position_equals(current_position, diamond.position) and
                self._is_in_scan_radius(current_position, diamond.position)):
                
                # Hitung jarak Manhattan
                distance = self._manhattan_distance(current_position, diamond.position)
                
                # Hitung nilai diamond dengan multiplier untuk red diamond
                diamond_value = diamond.properties.points
                if hasattr(diamond.properties, 'type') and diamond.properties.type == 'redDiamond':
                    diamond_value *= self.RED_DIAMOND_SCORE_MULTIPLIER
                
                # Hitung skor (nilai/jarak)
                current_score = diamond_value / (distance + 1)
                
                if current_score > best_score:
                    best_score = current_score
                    best_diamond = diamond

        return best_diamond

    def _manhattan_distance(self, pos1, pos2):
        """Menghitung jarak Manhattan antara dua posisi"""
        return abs(pos1.x - pos2.x) + abs(pos1.y - pos2.y)

    def _move_towards_goal(self, current_position, board):
        """Bergerak menuju tujuan dengan handling stuck"""
        cur_x, cur_y = current_position.x, current_position.y
        
        # Deteksi stuck
        if (cur_x, cur_y) == self.previous_position:
            self.stuck_counter += 1
        else:
            self.stuck_counter = 0

        # Jika stuck terlalu lama, lakukan random move
        if self.stuck_counter >= self.max_stuck_attempts:
            self.stuck_counter = 0
            self.goal_position = None  # Reset goal
            return self._random_move() # Menggunakan random_move saat stuck untuk mencoba keluar

        # Hitung arah ke tujuan
        delta_x, delta_y = get_direction(
            cur_x, cur_y,
            self.goal_position.x, self.goal_position.y
        )

        # Jika stuck, coba gerakan alternatif
        if (cur_x, cur_y) == self.previous_position and (delta_x != 0 or delta_y != 0):
            # Coba gerakan perpendicular
            if delta_x != 0:
                delta_y = delta_x * self.turn_direction
                delta_x = 0
            elif delta_y != 0:
                delta_x = delta_y * self.turn_direction
                delta_y = 0
            
            self.turn_direction *= -1  # Alternate direction

        # Validasi gerakan
        if not board.is_valid_move(current_position, delta_x, delta_y):
            # Jika gerakan tidak valid, coba random move
            return self._random_move()

        self.previous_position = (cur_x, cur_y)
        return delta_x, delta_y

    def _random_move(self):
        """Gerakan random murni (digunakan terutama untuk keluar dari stuck)"""
        moves = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        return random.choice(moves)

    def _semi_random_explore(self, current_position, board):
        """Gerakan semi-random untuk eksplorasi lebih terarah saat tidak ada tujuan"""
        delta_x, delta_y = self.exploration_direction
        
        # Coba bergerak sesuai arah eksplorasi saat ini
        if board.is_valid_move(current_position, delta_x, delta_y):
            self.previous_position = (current_position.x, current_position.y)
            return delta_x, delta_y
        else:
            # Jika tidak valid, coba gerakan acak lain untuk mencari arah baru
            valid_moves = []
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                if board.is_valid_move(current_position, dx, dy):
                    valid_moves.append((dx, dy))
            
            if valid_moves:
                new_direction = random.choice(valid_moves)
                self.exploration_direction = new_direction # Perbarui arah eksplorasi
                self.previous_position = (current_position.x, current_position.y)
                return new_direction
            else:
                # Terjebak sepenuhnya, tidak ada gerakan valid
                return 0, 0 # Tidak bergerak


    def _find_tackle_target_in_radius(self, board_bot: GameObject, board: Board):
        """Mencari bot musuh yang layak ditackling dalam SCAN_RADIUS"""
        
        # Cek apakah sudah ada target yang ditarget
        if self.targeted_enemy_id:
            for bot in board.game_objects:
                if bot.type == "BotGameObject" and bot.id == self.targeted_enemy_id:
                    # Jika target masih valid dan punya cukup berlian DAN dalam radius, terus kejar
                    if (bot.properties.diamonds >= self.tackle_threshold_diamonds and
                        self._is_in_scan_radius(board_bot.position, bot.position)):
                        return bot
                    else:
                        # Target tidak lagi valid (tidak di radius/tidak punya berlian cukup), reset
                        self.targeted_enemy_id = None
                        break

        # Cari target baru dalam radius
        best_target = None
        max_diamonds = self.tackle_threshold_diamonds - 1 # Minimum untuk memulai target

        for bot in board.game_objects:
            if bot.type == "BotGameObject" and bot.id != board_bot.id: # Bukan bot kita sendiri
                if (bot.properties.diamonds > max_diamonds and
                    self._is_in_scan_radius(board_bot.position, bot.position)): # Cek radius
                    max_diamonds = bot.properties.diamonds
                    best_target = bot
        
        # Hanya kembalikan target jika memenuhi tackle_threshold_diamonds
        if best_target and best_target.properties.diamonds >= self.tackle_threshold_diamonds:
            return best_target
        
        return None

    def _is_in_scan_radius(self, pos1, pos2):
        """Cek apakah posisi dalam radius scan"""
        return self._manhattan_distance(pos1, pos2) <= self.SCAN_RADIUS