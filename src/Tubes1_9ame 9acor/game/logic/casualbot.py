from typing import Optional, List
from game.logic.base import BaseLogic
from game.models import Board, GameObject, Position

class casualbot(BaseLogic):
    def __init__(self):
        self.target_destination: Optional[Position] = None
        self.is_teleporting_to_base_active = False
        self.return_to_base_count = 0 

    def find_nearest_diamond_by_points(self, bot_entity: GameObject, all_diamonds: List[GameObject], point_value_filter: Optional[int] = None) -> Optional[Position]:
        current_location = bot_entity.position
        
        filtered_diamond_list = all_diamonds
        if point_value_filter is not None:
            filtered_diamond_list = [d for d in all_diamonds if d.properties.points == point_value_filter]

        if not filtered_diamond_list:
            return None
        
        return min(filtered_diamond_list, key=lambda d: self.calculate_manhattan_distance(d.position, current_location)).position

    def calculate_manhattan_distance(self, location1: Position, location2: Position) -> int:
        return abs(location1.x - location2.x) + abs(location1.y - location2.y)

    def is_location_within_radius(self, check_pos: Position, center_pos: Position, max_radius: int) -> bool:
        return self.calculate_manhattan_distance(check_pos, center_pos) <= max_radius

    def get_bot_base_location(self, bot_entity: GameObject) -> Position:
        return bot_entity.properties.base

    def locate_red_button(self, game_board: Board) -> Optional[GameObject]:
        return next((item for item in game_board.game_objects if item.type == "DiamondButtonGameObject"), None)

    def locate_teleporters(self, game_board: Board) -> List[GameObject]:
        return [item for item in game_board.game_objects if item.type == "TeleportGameObject"]

    def evaluate_teleport_to_base(self, bot_entity: GameObject, game_board: Board) -> bool:
        current_location = bot_entity.position
        base_location = self.get_bot_base_location(bot_entity)
        
        all_teleporters = self.locate_teleporters(game_board)
        if len(all_teleporters) < 2:
            return False

        closest_teleporter = min(all_teleporters, key=lambda tele: self.calculate_manhattan_distance(tele.position, current_location))
        
        teleporter_leading_to_base_exit = min(all_teleporters, key=lambda tele: self.calculate_manhattan_distance(tele.position, base_location))

        distance_to_base_direct = self.calculate_manhattan_distance(current_location, base_location)
        distance_to_closest_teleporter = self.calculate_manhattan_distance(current_location, closest_teleporter.position)
        distance_from_teleporter_to_base = self.calculate_manhattan_distance(teleporter_leading_to_base_exit.position, base_location)

        if bot_entity.properties.diamonds >= 3 and distance_to_base_direct > 5:
            if distance_to_closest_teleporter <= 3 and (distance_to_closest_teleporter + distance_from_teleporter_to_base < distance_to_base_direct):
                self.target_destination = closest_teleporter.position
                self.is_teleporting_to_base_active = True
                return True
        return False

    def next_move(self, bot_entity: GameObject, game_board: Board):
        current_location = bot_entity.position
        base_location = self.get_bot_base_location(bot_entity)
        bot_current_diamonds = bot_entity.properties.diamonds
        
        self.target_destination = None 

        if current_location == base_location and bot_current_diamonds == 0:
             self.return_to_base_count += 1
             self.is_teleporting_to_base_active = False

        if self.is_teleporting_to_base_active and self.target_destination is not None and current_location == self.target_destination:
            self.is_teleporting_to_base_active = False

        time_left_ms = bot_entity.properties.milliseconds_left

        if bot_current_diamonds == 5:
            self.target_destination = base_location
        elif time_left_ms < 5000:
            self.target_destination = base_location
        elif time_left_ms < 15000 and bot_current_diamonds > 0:
            self.target_destination = base_location
        elif bot_current_diamonds >= 4 or (bot_current_diamonds >= 2 and self.calculate_manhattan_distance(current_location, base_location) <= 2):
            self.target_destination = base_location
        
        if self.target_destination is None and bot_current_diamonds < 5: 
            blue_diamond_location = self.find_nearest_diamond_by_points(bot_entity, game_board.diamonds, point_value_filter=1)
            red_diamond_location = self.find_nearest_diamond_by_points(bot_entity, game_board.diamonds, point_value_filter=2)
            red_button_object = self.locate_red_button(game_board)

            if len(game_board.diamonds) < 3 and red_button_object and \
               self.is_location_within_radius(current_location, red_button_object.position, 3):
                self.target_destination = red_button_object.position
            elif red_diamond_location and self.is_location_within_radius(current_location, red_diamond_location, 2):
                self.target_destination = red_diamond_location
            elif blue_diamond_location:
                self.target_destination = blue_diamond_location
            else: 
                self.target_destination = base_location

        if self.target_destination is None:
            red_button_object = self.locate_red_button(game_board)
            if red_button_object and self.is_location_within_radius(current_location, red_button_object.position, 3):
                closest_diamond_any_type = self.find_nearest_diamond_by_points(bot_entity, game_board.diamonds)
                if not closest_diamond_any_type or \
                   self.calculate_manhattan_distance(current_location, red_button_object.position) < self.calculate_manhattan_distance(current_location, closest_diamond_any_type):
                    self.target_destination = red_button_object.position

        if self.target_destination is None:
            self.target_destination = base_location

        if self.target_destination == base_location and not self.is_teleporting_to_base_active:
            self.evaluate_teleport_to_base(bot_entity, game_board)

        delta_x, delta_y = 0, 0

        if current_location.x == self.target_destination.x and current_location.y == self.target_destination.y:
            return 0, 0

        if self.target_destination.x > current_location.x:
            delta_x = 1
        elif self.target_destination.x < current_location.x:
            delta_x = -1
        
        if self.target_destination.y > current_location.y:
            delta_y = 1
        elif self.target_destination.y < current_location.y:
            delta_y = -1
        
        if delta_x != 0 and delta_y != 0:
            if abs(self.target_destination.x - current_location.x) >= abs(self.target_destination.y - current_location.y):
                delta_y = 0
            else:
                delta_x = 0
        
        return delta_x, delta_y