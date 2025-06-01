import random
from game.logic.base import BaseLogic
from game.models import Board, GameObject, Position, Properties # Pastikan Properties diimpor
from game.util import get_direction, position_equals
from typing import Optional, List, Tuple

class superbot(BaseLogic):
    def __init__(self):
        self.directions = [(1, 0), (0,1), (-1,0), (0, -1)]
        self.goal_position: Optional[Position] = None
        self.is_teleport = False
        self.langkah = 0
        self.arah_saat_ini = 0
        
        self.target_tackle_id: Optional[str] = None
        self.target_tackle_position: Optional[Position] = None
        self.tackle_threshold_diamonds = 3
        self.SCAN_RADIUS = 10

        self.previous_position: Optional[Tuple[int, int]] = None
        self.stuck_counter = 0
        self.max_stuck_attempts = 3
        self.exploration_direction = random.choice(self.directions)
        
        self.RED_DIAMOND_SCORE_MULTIPLIER = 2.0


    def get_distance(self, pos1: Position, pos2: Position) -> int:
        return abs(pos1.x - pos2.x) + abs(pos1.y - pos2.y)

    def _is_in_scan_radius(self, pos1: Position, pos2: Position) -> bool:
        return self.get_distance(pos1, pos2) <= self.SCAN_RADIUS

    def find_nearest_diamond(self, bot_position: Position, diamonds: List[GameObject], points_filter: Optional[int] = None) -> Optional[Position]:
        filtered_diamonds = diamonds
        if points_filter is not None:
            filtered_diamonds = [d for d in diamonds if d.properties.points == points_filter]

        if not filtered_diamonds:
            return None
        
        return min(filtered_diamonds, key=lambda d: self.get_distance(d.position, bot_position)).position

    # Perbaikan: Type hint untuk props diubah dari GameObject.Properties menjadi Properties
    def _find_best_diamond_in_radius(self, current_position: Position, props: Properties, board: Board) -> Optional[GameObject]:
        best_score = -1.0
        best_diamond = None
        space_left = props.inventory_size - props.diamonds

        for diamond in board.diamonds:
            if (diamond.properties.points <= space_left and 
                not position_equals(current_position, diamond.position) and
                self._is_in_scan_radius(current_position, diamond.position)):
                
                distance = self.get_distance(current_position, diamond.position)
                
                diamond_value = diamond.properties.points
                if hasattr(diamond.properties, 'type') and diamond.properties.type == 'redDiamond':
                    diamond_value *= self.RED_DIAMOND_SCORE_MULTIPLIER
                
                current_score = diamond_value / (distance + 1)
                
                if current_score > best_score:
                    best_score = current_score
                    best_diamond = diamond
        return best_diamond

    def get_teleport_target(self, bot_position: Position, base_position: Position, game_objects: List[GameObject]) -> Tuple[Optional[Position], bool]:
        teleporters = [item for item in game_objects if item.type == "TeleportGameObject"]
        
        if len(teleporters) < 2: 
            return None, False

        t1 = teleporters[0]
        t2 = teleporters[1]

        # Hitung jarak gabungan untuk kedua rute teleportasi
        dist_route1 = self.get_distance(bot_position, t1.position) + self.get_distance(t2.position, base_position)
        dist_route2 = self.get_distance(bot_position, t2.position) + self.get_distance(t1.position, base_position)
        
        dist_bot_to_base_direct = self.get_distance(bot_position, base_position)

        # Perbaikan: Gunakan key pada min() untuk membandingkan berdasarkan jarak, bukan objek Position
        distances_with_keys = []
        distances_with_keys.append((dist_route1, t1.position))
        distances_with_keys.append((dist_route2, t2.position))

        min_combined_dist, best_tp_pos = min(distances_with_keys, key=lambda x: x[0]) # Membandingkan berdasarkan elemen pertama (jarak)
        
        if min_combined_dist < dist_bot_to_base_direct:
            return best_tp_pos, True
        
        return None, False

    def find_diamond_button(self, game_objects: List[GameObject]) -> Optional[Position]:
        for obj in game_objects:
            if obj.type == "DiamondButtonGameObject":
                return obj.position
        return None

    def find_enemy_bots(self, my_bot_id: str, bots: List[GameObject]) -> List[GameObject]:
        return [bot for bot in bots if bot.id != my_bot_id]
    
    def get_tackle_position(self, my_position: Position, enemy_position: Position) -> Position:
        if position_equals(my_position, enemy_position):
            return my_position 

        if self.get_distance(my_position, enemy_position) == 1:
            return enemy_position

        delta_x_step = 0
        delta_y_step = 0

        if my_position.x < enemy_position.x:
            delta_x_step = 1
        elif my_position.x > enemy_position.x:
            delta_x_step = -1
        
        if my_position.y < enemy_position.y:
            delta_y_step = 1
        elif my_position.y > enemy_position.y:
            delta_y_step = -1
        
        if abs(my_position.x - enemy_position.x) >= abs(my_position.y - enemy_position.y):
            return Position(my_position.x + delta_x_step, my_position.y)
        else:
            return Position(my_position.x, my_position.y + delta_y_step)

    def _random_move(self) -> Tuple[int, int]:
        moves = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        return random.choice(moves)

    def _semi_random_explore(self, current_position: Position, board: Board) -> Tuple[int, int]:
        delta_x, delta_y = self.exploration_direction
        
        if board.is_valid_move(current_position, delta_x, delta_y):
            self.previous_position = (current_position.x, current_position.y)
            return delta_x, delta_y
        else:
            valid_moves = []
            for dx, dy in self.directions:
                if board.is_valid_move(current_position, dx, dy):
                    valid_moves.append((dx, dy))
            
            if valid_moves:
                new_direction = random.choice(valid_moves)
                self.exploration_direction = new_direction
                self.previous_position = (current_position.x, current_position.y)
                return new_direction
            else:
                return 0, 0

    def _find_tackle_target_in_radius(self, board_bot: GameObject, board: Board) -> Optional[GameObject]:
        if self.target_tackle_id:
            targeted_bot = next((b for b in board.bots if b.id == self.target_tackle_id), None)
            if targeted_bot:
                if (targeted_bot.properties.diamonds >= self.tackle_threshold_diamonds and
                    self._is_in_scan_radius(board_bot.position, targeted_bot.position)):
                    return targeted_bot
            self.target_tackle_id = None
            self.target_tackle_position = None

        best_target = None
        max_diamonds_found = self.tackle_threshold_diamonds - 1

        for bot in board.bots:
            if bot.id != board_bot.id and \
               bot.properties.diamonds > max_diamonds_found and \
               self._is_in_scan_radius(board_bot.position, bot.position):
                max_diamonds_found = bot.properties.diamonds
                best_target = bot
        
        return best_target


    def next_move(self, board_bot: GameObject, board: Board) -> Tuple[int, int]:
        props = board_bot.properties
        current_position = board_bot.position
        base = props.base
        self.goal_position = None 

        current_pos_tuple = (current_position.x, current_position.y)
        if self.previous_position == current_pos_tuple:
            self.stuck_counter += 1
        else:
            self.stuck_counter = 0
        self.previous_position = current_pos_tuple

        if self.stuck_counter >= self.max_stuck_attempts:
            self.stuck_counter = 0
            self.goal_position = None
            self.target_tackle_id = None
            self.target_tackle_position = None
            return self._random_move()

        if self.target_tackle_id and (props.diamonds == 5 or position_equals(current_position, base)):
            self.target_tackle_id = None
            self.target_tackle_position = None

        if props.diamonds == 5 or props.milliseconds_left < 7000:
            self.goal_position = base
            target_teleport_pos, do_teleport = self.get_teleport_target(current_position, base, board.game_objects)
            if do_teleport:
                self.goal_position = target_teleport_pos
                self.is_teleport = True
            else:
                self.is_teleport = False
        
        elif props.diamonds <= 2 and props.milliseconds_left > 15000:
            tackle_target_candidate = self._find_tackle_target_in_radius(board_bot, board)
            
            if tackle_target_candidate:
                self.target_tackle_id = tackle_target_candidate.id
                self.target_tackle_position = tackle_target_candidate.position

            if self.target_tackle_id and self.target_tackle_position:
                current_target_bot = next((b for b in board.bots if b.id == self.target_tackle_id), None)
                if current_target_bot:
                    self.target_tackle_position = current_target_bot.position 
                    
                    if self.get_distance(current_position, self.target_tackle_position) <= 1:
                        self.goal_position = self.get_tackle_position(current_position, self.target_tackle_position)
                    else:
                        self.goal_position = self.target_tackle_position
                else:
                    self.target_tackle_id = None
                    self.target_tackle_position = None
                    self.goal_position = None

        if self.goal_position is None:
            best_diamond_in_radius = self._find_best_diamond_in_radius(current_position, props, board)

            if best_diamond_in_radius:
                self.goal_position = best_diamond_in_radius.position
            else:
                diamond_button_pos = self.find_diamond_button(board.game_objects)
                if diamond_button_pos and self.get_distance(current_position, diamond_button_pos) < self.SCAN_RADIUS:
                    self.goal_position = diamond_button_pos
                elif props.diamonds > 0:
                    self.goal_position = base
                else:
                    self.goal_position = None
                    self.exploration_direction = random.choice(self.directions)

        if self.goal_position is None:
            delta_x, delta_y = self._semi_random_explore(current_position, board)
        else:
            delta_x, delta_y = get_direction(
                current_position.x,
                current_position.y,
                self.goal_position.x,
                self.goal_position.y,
            )

            # Penanganan untuk Gerakan (0,0) yang game anggap "delta_x == delta_y"
            # Karena get_direction dari util.py sudah memastikan delta_x atau delta_y akan 0 (tidak diagonal).
            if delta_x == 0 and delta_y == 0:
                # Jika sudah di tujuan (delta 0,0), dan game melarang (0,0), paksa random walk
                delta_x, delta_y = self.directions[self.arah_saat_ini]
                self.arah_saat_ini = (self.arah_saat_ini + 1) % len(self.directions)

        if self.is_teleport and not position_equals(current_position, self.goal_position):
             self.is_teleport = False

        return delta_x, delta_y