from typing import Optional
from typing import List
from game.logic.base import BaseLogic
from game.models import Board, GameObject, Position

class gacorbot(BaseLogic):
    def __init__(self):
        self.arah = [(1, 0), (0,1), (-1,0), (0, -1)]
        self.goal_position: Optional[Position] = None
        self.is_teleport = False
        self.langkah = 0
        self.arah_saat_ini = 0

    def diamond_dekat_base(self, bot_papan: GameObject, papan: Board, jarak: int = 4):
        gcor = bot_papan.properties.base
        diamond = papan.diamonds
        if not gcor:
            return []

        return [
            diamond.position for diamond in diamond
            if ((gcor.x - jarak <= diamond.position.x <= gcor.x + jarak) and
                (gcor.y - jarak <= diamond.position.y <= gcor.y + jarak))
        ]
    
    def botsekitarbase(self, bot_papan: GameObject, jarak: int = 4):
        gcor = bot_papan.properties.base
        posisi_saat_ini = bot_papan.position
        return ((gcor.x - jarak <= posisi_saat_ini.x <= gcor.x + jarak) and 
                (gcor.y - jarak <= posisi_saat_ini.y <= gcor.y + jarak))
    
    def diamonddekatbot(self, bot_papan: GameObject, diamonds: List[Position]):
        posisi_saat_ini = bot_papan.position
        diamond_terdekat = min(diamonds, key=lambda diamond: abs(diamond.x - posisi_saat_ini.x) + abs(diamond.y - posisi_saat_ini.y))
        return diamond_terdekat
    
    def diamondsekitarbase(self, bot_papan: GameObject, papan: Board, jarak: int = 2):
        diamonds = papan.diamonds
        gcor = bot_papan.properties.base

        if not gcor:
            return False  
        
        for diamond in diamonds:
            if ((gcor.x - jarak) <= diamond.position.x <= (gcor.x + jarak) and 
               (gcor.y - jarak) <= diamond.position.y <= (gcor.y + jarak)):
                return True  
        
        return False

    def diamond_terdekat(self, bot_papan: GameObject, papan: Board):
        posisi_saat_ini = bot_papan.position
        diamond_biru = [d for d in papan.diamonds if d.properties.points == 1]
        if not diamond_biru:
            return None
        
        return min(diamond_biru, key=lambda d: abs(d.position.x - posisi_saat_ini.x) + abs(d.position.y - posisi_saat_ini.y)).position if diamond_biru else None

    def jarak_diamond_dekat(self, bot_papan: GameObject, papan: Board):
        terdekat = self.diamond_terdekat(bot_papan, papan)
        return 999 if terdekat is None else abs(terdekat.x - bot_papan.position.x) + abs(terdekat.y - bot_papan.position.y)
    
    def diamondmerah_terdekat(self, bot_papan: GameObject, papan: Board):
        posisi_saat_ini = bot_papan.position
        diamond_merah = [d for d in papan.diamonds if d.properties.points == 2]
        if not diamond_merah:
            return None

        return min(diamond_merah, key=lambda d: abs(d.position.x - posisi_saat_ini.x) + abs(d.position.y - posisi_saat_ini.y)).position if diamond_merah else None

    def jarak_diamondmerah_dekat(self, bot_papan: GameObject, papan: Board):
        terdekat = self.diamondmerah_terdekat(bot_papan, papan)
        return 999 if terdekat is None else abs(terdekat.x - bot_papan.position.x) + abs(terdekat.y - bot_papan.position.y)
    
    def jarakbase(self, bot_papan: GameObject):
        base, pos = bot_papan.properties.base, bot_papan.position
        return abs(base.x - pos.x) + abs(base.y - pos.y)

    def hitungjarak(self, pos1, pos2):
        return abs(pos1.x - pos2.x) + abs(pos1.y - pos2.y)

    def caribotlain(self, bot_papan: GameObject, papan: Board):
        return [bot for bot in papan.bots if bot.id != bot_papan.id 
                and bot.properties.base != bot.position
                and bot.properties.diamonds >= 3 
                and bot.properties.diamonds > bot_papan.properties.diamonds]

    def kejar_bot_musuh(self, bot_papan: GameObject, papan: Board):
        if self.jarakbase(bot_papan) > 4 or self.langkah > 5:
            self.goal_position, self.langkah, self.is_teleport = None, 0, False
            return False

        for bot in self.caribotlain(bot_papan, papan):
            dist = self.hitungjarak(bot_papan.position, bot.position)
            if dist == 0:
                self.goal_position = bot_papan.properties.base  
                return False
            elif dist <= 3:
                self.goal_position = bot.position 
                return True

        self.goal_position = None
        return False

    def caritmblmrh(self, papan: Board):
        return next((item for item in papan.game_objects if item.type == "DiamondButtonGameObject"), None)

    def hitungjaraktmblmrh(self, bot_papan: GameObject, papan: Board):
        tmblmrh = self.caritmblmrh(papan)
        return (abs(tmblmrh.position.x - bot_papan.position.x) + abs(tmblmrh.position.y - bot_papan.position.y)) if tmblmrh else float('inf')

    def jarak_diamond_tmblmrh(self, bot_papan: GameObject, papan: Board):
        tmblmrh = self.caritmblmrh(papan)

        if not tmblmrh:
            return False

        diamond_biru_terdekat = self.diamond_terdekat(bot_papan, papan)
        if not diamond_biru_terdekat:
            return False

        return self.hitungjaraktmblmrh(bot_papan, papan) < self.jarak_diamond_dekat(bot_papan, papan)
    
    def cariteleporter(self, bot_papan: GameObject, papan: Board):
        teleporters = [item for item in papan.game_objects if item.type == "TeleportGameObject"]
        return sorted(teleporters, key=lambda tele: self.hitungjarak(tele.position, bot_papan.position))

    def teleport_ke_base(self, bot_papan: GameObject, papan: Board):
        teleporters = self.cariteleporter(bot_papan, papan)

        if len(teleporters) < 2: 
            return

        teleporter_dekat = teleporters[0]
        teleporter_baik = min(teleporters, key=lambda tele: self.hitungjarak(tele.position, bot_papan.properties.base))

        jarakkeBase = self.hitungjarak(teleporter_baik.position, bot_papan.properties.base)
        jarakkebot = self.hitungjarak(bot_papan.position, teleporter_dekat.position)

        if jarakkebot <= 5 and jarakkeBase + jarakkebot < self.jarakbase(bot_papan):
            self.is_teleport= True
            self.goal_position = teleporter_dekat.position

    def peroleh_jarak(self, current_x, current_y, dest_x, dest_y):
        x = -1 if dest_x < current_x else 1
        y = -1 if dest_y < current_y else 1

        dx, dy = (x, 0) if abs(dest_x - current_x) >= abs(dest_y - current_y) else (0, y)
        return dx, dy

    def next_move(self, board_bot: GameObject, board: Board):
        gcor = board_bot.properties
        posisi_saat_ini = board_bot.position
        base = gcor.base

        if self.jarakbase(board_bot) in {gcor.milliseconds_left, 2} and gcor.diamonds > 2 or \
            self.jarakbase(board_bot) == 1 and gcor.diamonds > 0 or gcor.diamonds == 5:
            self.goal_position = base

        elif gcor.diamonds >= 3:
            if self.diamond_terdekat(board_bot, board) is not None or self.diamondmerah_terdekat(board_bot, board) is not None:
                if gcor.diamonds == 3 and self.jarak_diamondmerah_dekat(board_bot, board) <= 3:
                    self.goal_position = self.diamondmerah_terdekat(board_bot, board)
                elif self.jarak_diamond_dekat(board_bot, board) <= 3:
                    self.goal_position = self.diamond_terdekat(board_bot, board)
                else:
                    base = board_bot.properties.base
                    self.goal_position = base
            elif self.diamondsekitarbase(board_bot, board):
                diamond_list = self.diamond_dekat_base(board_bot, board)
                self.goal_position = self.diamonddekatbot(board_bot, diamond_list)
            else:
                base = board_bot.properties.base
                self.goal_position = base

        elif gcor.diamonds < 3:
            if (self.diamondsekitarbase(board_bot, board) and self.botsekitarbase(board_bot)) or (
                self.diamondsekitarbase(board_bot, board) and len(self.diamond_dekat_base(board_bot, board)) >= 3
            ):
                diamond_list = self.diamond_dekat_base(board_bot, board)
                self.goal_position = self.diamonddekatbot(board_bot, diamond_list)
            elif self.diamondmerah_terdekat(board_bot, board) is not None:
                if self.diamond_terdekat(board_bot, board) is not None:
                    if self.jarak_diamondmerah_dekat(board_bot, board) <= 3:
                        self.goal_position = self.diamondmerah_terdekat(board_bot, board)
                    else:
                        self.goal_position = self.diamond_terdekat(board_bot, board)
                else:
                    self.goal_position = self.diamondmerah_terdekat(board_bot, board)
            elif self.diamond_terdekat(board_bot, board) is not None:
                self.goal_position = self.diamond_terdekat(board_bot, board)

            elif self.jarak_diamond_tmblmrh(board_bot, board):
                self.goal_position = self.caritmblmrh(board).position

            else:
                self.goal_position = board_bot.properties.base

        if self.goal_position is None:
            self.goal_position = base

        if self.goal_position == base and not self.is_teleport:
            self.teleport_ke_base(board_bot, board)

        delta_x, delta_y = self.peroleh_jarak(
            posisi_saat_ini.x, posisi_saat_ini.y,
            self.goal_position.x, self.goal_position.y
        )

        return delta_x, delta_y