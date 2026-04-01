# agents/base_agent.py
from typing import Optional
from core.state import GameState
from core.move import Move
from core.rules import Color

class BaseAgent:
    def __init__(self, player_id: Color, name: str = "BaseAgent"):
        self.player_id = player_id
        self.name = name

    def select_move(self, state: GameState) -> Optional[Move]:   
        raise NotImplementedError() 