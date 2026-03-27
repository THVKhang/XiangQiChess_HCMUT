# agents/base_agent.py
from typing import Optional
from core.state import GameState
from core.move import Move
from core.rules import Color

class BaseAgent:
    """
    Lớp cơ sở bắt buộc cho mọi Agent.
    """
    def __init__(self, player_id: Color, name: str = "BaseAgent"):
        self.player_id = player_id
        self.name = name

    def select_move(self, state: GameState) -> Optional[Move]:   
        """
        Nhận vào trạng thái game và trả về một nước đi.
        """
        raise NotImplementedError("Phải ghi đè hàm select_move ở lớp con.") 