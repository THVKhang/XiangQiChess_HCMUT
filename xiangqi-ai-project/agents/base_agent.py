# agents/base_agent.py

class BaseAgent:
    """
    Lớp cơ sở bắt buộc cho mọi Agent.
    """
    def __init__(self, player_id):
        self.player_id = player_id

    def select_move(self, state):   
        """
        Nhận vào trạng thái game và trả về một nước đi.
        """
        raise NotImplementedError("Phải ghi đè hàm select_move ở lớp con.") 