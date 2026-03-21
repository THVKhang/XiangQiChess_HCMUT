import time
from agents.base_agent import BaseAgent
from core.move_generator import legal_moves

class MinimaxAgent(BaseAgent):
    """
    Agent sử dụng thuật toán Minimax cơ bản (không cắt tỉa) để chọn nước đi.
    """
    def __init__(self, player_id, depth=3):
        super().__init__(player_id)
        self.depth = depth

    def get_action(self, state):
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
        """
        Hàm lượng giá (Heuristic function) đánh giá chất lượng của một trạng thái bàn cờ.
        """
        score = 0
        return score


class AlphaBetaAgent(BaseAgent):
    """
    Agent sử dụng thuật toán Alpha-Beta Pruning để chọn nước đi tối ưu hơn.
    """
    def __init__(self, player_id, depth=3):
        super().__init__(player_id)
        self.depth = depth

    def get_action(self, state):
        best_move = None
        best_score = float('-inf')
        alpha = float('-inf')
        beta = float('inf')

        moves = legal_moves(state)
        
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
        """
        Hàm lượng giá (Heuristic function) đánh giá chất lượng của một trạng thái bàn cờ.
        """
        score = 0
        return score

if __name__ == "__main__":
    from core.state import GameState
    from core.rules import Color
    
    print("Khởi tạo bàn cờ giả (trạng thái ban đầu)...")
    st = GameState()
    
    print("Khởi tạo MinimaxAgent (độ sâu = 2)...")
    # Độ sâu 2 để test nhanh xem khung có chạy mượt mà không
    agent = MinimaxAgent(player_id=Color.RED, depth=2)
    
    print("Đang tìm nhánh bằng Minimax...")
    start_time = time.time()
    move = agent.get_action(st)
    end_time = time.time()
    
    print(f"Hoàn tất! Thuật toán đã chọn nước đi: {move}")
    print(f"Thời gian chạy bộ khung MiniMax: {end_time - start_time:.4f} giây")
