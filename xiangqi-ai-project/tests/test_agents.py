from core.state import GameState
from core.rules import Color
from agents.search_agent import MinimaxAgent, AlphaBetaAgent

def test_minimax_agent():
    state = GameState()
    # Khởi tạo Minimax với độ sâu nhỏ để test nhanh
    agent = MinimaxAgent(player_id=Color.RED, depth=2)
    
    move = agent.get_action(state)
    
    # Ở state ban đầu, nước đi không thể là None
    assert move is not None
    print(f"Minimax decided: {move}")


def test_alphabeta_agent():
    state = GameState()
    # Khởi tạo AlphaBeta với độ sâu lớn hơn chút xíu để thấy prune
    agent = AlphaBetaAgent(player_id=Color.RED, depth=3)
    
    move = agent.get_action(state)
    
    assert move is not None
    print(f"AlphaBeta decided: {move}")


def test_agent_consistency():
    state = GameState()
    # Vì evaluate trả về 0 hết nên có thể 2 agent chọn 2 nước đi khác nhau
    # Tuy nhiên, ta vẫn test để đảm bảo chúng không bị crash
    agent1 = MinimaxAgent(player_id=Color.RED, depth=2)
    agent2 = AlphaBetaAgent(player_id=Color.RED, depth=2)
    
    move1 = agent1.get_action(state.clone())
    move2 = agent2.get_action(state.clone())
    
    assert move1 is not None
    assert move2 is not None
    # Lưu ý: Cả hai đều có thể trả về nước đi do đánh giá 0 đều ngang nhau
    # Nên không nhất thiết phải assert move1 == move2, tuỳ thuộc thuật toán cắt tỉa.

if __name__ == "__main__":
    print("--- Running test_minimax_agent ---")
    test_minimax_agent()
    
    print("\n--- Running test_alphabeta_agent ---")
    test_alphabeta_agent()
    
    print("\n--- Running test_agent_consistency ---")
    test_agent_consistency()
    
    print("\nAll tests passed!")
