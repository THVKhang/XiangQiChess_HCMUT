import time
from typing import Optional

from agents.base_agent import BaseAgent
from core.move_generator import legal_moves
from core.state import GameState
from core.move import Move
from core.rules import Color, PieceType, on_own_side_of_river

# Bảng giá trị cơ bản của các quân cờ
PIECE_VALUES = {
    PieceType.GENERAL: 10000,
    PieceType.ROOK: 900,
    PieceType.CANNON: 450,
    PieceType.HORSE: 400,
    PieceType.ELEPHANT: 200,
    PieceType.ADVISOR: 200,
    PieceType.SOLDIER: 100
}

def basic_evaluate(state: GameState, player_id):
    """
    Hàm lượng giá cơ bản. Chỉ dựa vào giá trị quân.
    """
    score = 0
    for pos, piece in state.board.squares():
        if piece is None:
            continue
        val = PIECE_VALUES.get(piece.kind, 0)
        if piece.color == player_id:
            score += val
        else:
            score -= val
    return score


def advanced_evaluate(state: GameState, player_id):
    """
    Hàm lượng giá nâng cao (Heuristic bản 2: Giá trị quân + Vị trí chiến lược)
    """
    score = 0
    for pos, piece in state.board.squares():
        if piece is None:
            continue
        
        r, c = pos
        val = PIECE_VALUES.get(piece.kind, 0)
        
        # 1. Tốt (Pawn)
        if piece.kind == PieceType.SOLDIER:
            if not on_own_side_of_river(piece.color, pos):
                val += 100  # Tốt qua sông
                # Thưởng nếu áp sát cung Tướng địch nhưng chưa bị lụt (xuống đáy)
                # Đỏ đi từ hàng 9 -> 0, Đen đi từ 0 -> 9
                if piece.color == Color.RED:
                    if 1 <= r <= 2 and 3 <= c <= 5: val += 50
                    elif r == 0: val -= 30
                else:
                    if 7 <= r <= 8 and 3 <= c <= 5: val += 50
                    elif r == 9: val -= 30
                    
        # 2. Mã (Horse)
        elif piece.kind == PieceType.HORSE:
            if c == 0 or c == 8: val -= 20   # Mã biên bị giới hạn
            elif 3 <= c <= 5: val += 20      # Mã trung tâm mạnh hơn

        # 3. Pháo (Cannon)
        elif piece.kind == PieceType.CANNON:
            if c == 4: val += 30             # Pháo khống chế lộ giữa nguy hiểm

        # 4. Xe (Rook)
        elif piece.kind == PieceType.ROOK:
            if c in (2, 4, 6): val += 15     # Xe đóng ở các trục quan trọng
            
        if piece.color == player_id:
            score += val
        else:
            score -= val
            
    return score

class MinimaxAgent(BaseAgent):
    """
    Agent sử dụng thuật toán Minimax cơ bản (không cắt tỉa) để chọn nước đi.
    """
    def __init__(self, player_id, name="MinimaxAgent", depth=3):
        super().__init__(player_id, name)
        self.depth = depth

    def select_move(self, state: GameState) -> Optional[Move]:
        best_move = None
        best_score = float('-inf')

        # Dùng API legal_moves (hoặc generate_legal_moves) từ core
        moves = legal_moves(state)
        
        for move in moves:
            # Clone state hiện tại để thử nghiệm nước đi
            next_state = state.clone()
            next_state.apply_move(move)
            
            # apply_move sẽ tự động đổi lượt trong state, 
            # nên state kế tiếp thuộc về đối thủ (MIN)
            score = self.minimax(next_state, self.depth - 1, False)
            
            if score > best_score:
                best_score = score
                best_move = move
                    
        return best_move

    def minimax(self, state, depth, is_maximizing_player):
        # Nếu đạt độ sâu tối đa hoặc trận đấu kết thúc
        if depth == 0 or state.is_terminal():
            return self.evaluate(state)

        moves = legal_moves(state)
        # Nếu không còn nước đi hợp lệ (bị chiếu bí hoặc cờ hòa)
        if not moves:
            return self.evaluate(state)

        if is_maximizing_player:
            best_score = float('-inf')
            for move in moves:
                next_state = state.clone()
                next_state.apply_move(move)
                score = self.minimax(next_state, depth - 1, False)
                best_score = max(best_score, score)
            return best_score
        else:
            best_score = float('inf')
            for move in moves:
                next_state = state.clone()
                next_state.apply_move(move)
                score = self.minimax(next_state, depth - 1, True)
                best_score = min(best_score, score)
            return best_score

    def evaluate(self, state):
        return evaluate_state(state, self.player_id)


class AlphaBetaAgent(BaseAgent):
    """
    Agent sử dụng thuật toán Alpha-Beta Pruning để chọn nước đi tối ưu hơn.
    """
    def __init__(self, player_id, name="AlphaBetaAgent", depth=3, use_move_ordering=False):
        super().__init__(player_id, name)
        self.depth = depth
        self.use_move_ordering = use_move_ordering

    def order_moves(self, state, moves):
        if not self.use_move_ordering:
            return moves
            
        def move_score(move):
            target_piece = state.board.get(move.dst)
            if target_piece is not None:
                return PIECE_VALUES.get(target_piece.kind, 0)
            return 0
            
        return sorted(moves, key=move_score, reverse=True)

    def select_move(self, state: GameState) -> Optional[Move]:
        best_move = None
        best_score = float('-inf')
        alpha = float('-inf')
        beta = float('inf')

        moves = legal_moves(state)
        moves = self.order_moves(state, moves)
        
        for move in moves:
            next_state = state.clone()
            next_state.apply_move(move)
            
            score = self.alpha_beta(next_state, self.depth - 1, alpha, beta, False)
            
            if score > best_score:
                best_score = score
                best_move = move
            
            alpha = max(alpha, best_score)
                    
        return best_move

    def alpha_beta(self, state, depth, alpha, beta, is_maximizing_player):
        if depth == 0 or state.is_terminal():
            return self.evaluate(state)

        moves = legal_moves(state)
        moves = self.order_moves(state, moves)
        if not moves:
            return self.evaluate(state)

        if is_maximizing_player:
            best_score = float('-inf')
            for move in moves:
                next_state = state.clone()
                next_state.apply_move(move)
                score = self.alpha_beta(next_state, depth - 1, alpha, beta, False)
                best_score = max(best_score, score)
                alpha = max(alpha, best_score)
                if beta <= alpha:
                    break   # Cắt tỉa Beta
            return best_score
        else:
            best_score = float('inf')
            for move in moves:
                next_state = state.clone()
                next_state.apply_move(move)
                score = self.alpha_beta(next_state, depth - 1, alpha, beta, True)
                best_score = min(best_score, score)
                beta = min(beta, best_score)
                if beta <= alpha:
                    break   # Cắt tỉa Alpha
            return best_score

    def evaluate(self, state):
        return advanced_evaluate(state, self.player_id)

def get_level_config(level: int):
    # Trả về: (depth, use_advanced_heuristic, use_move_ordering)
    configs = {
        1: (1, False, False),
        2: (1, True, False),
        3: (2, False, False),
        4: (2, True, False),
        5: (2, True, True),
        6: (3, False, False),
        7: (3, True, False),
        8: (3, True, True),
        9: (4, True, False),
        10: (4, True, True),
    }
    return configs[max(1, min(10, level))]

class LevelAgent(AlphaBetaAgent):
    """Agent có định mức kỹ năng từ 1-10 (poor -> good)"""
    def __init__(self, player_id, level=1, name=None):
        self.level = max(1, min(10, level))
        depth, self.use_advanced, use_ord = get_level_config(self.level)
        agent_name = name or f"LevelAgent(Lvl {self.level})"
        super().__init__(player_id, name=agent_name, depth=depth, use_move_ordering=use_ord)
        
    def evaluate(self, state):
        if self.use_advanced:
            return advanced_evaluate(state, self.player_id)
        return basic_evaluate(state, self.player_id)

class EasyAgent(LevelAgent):
    """Bí danh cho Level 1 (Kém nhất)"""
    def __init__(self, player_id, name="EasyAgent"):
        super().__init__(player_id, level=1, name=name)

class MediumAgent(LevelAgent):
    """Bí danh cho Level 4 (Trung bình)"""
    def __init__(self, player_id, name="MediumAgent"):
        super().__init__(player_id, level=4, name=name)

class HardAgent(LevelAgent):
    """Bí danh cho Level 8 (Xuất sắc)"""
    def __init__(self, player_id, name="HardAgent"):
        super().__init__(player_id, level=8, name=name)

if __name__ == "__main__":
    from core.state import GameState
    from core.rules import Color
    
    print("Khởi tạo bàn cờ giả (trạng thái ban đầu)...")
    st = GameState()
    
    print("Khởi tạo LevelAgent(level=5)...")
    agent = LevelAgent(player_id=Color.RED, level=5)
    
    print(f"Đang tìm nhánh bằng {agent.name} (Depth {agent.depth}, Ord: {agent.use_move_ordering})...")
    start_time = time.time()
    move = agent.select_move(st)
    end_time = time.time()
    
    print(f"Hoàn tất! Thuật toán đã chọn nước đi: {move}")
    print(f"Thời gian chạy bộ khung {agent.name}: {end_time - start_time:.4f} giây")
