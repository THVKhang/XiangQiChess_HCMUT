from core.state import GameState
from core.rules import Color
from agents.search_agent import EasyAgent, MediumAgent, HardAgent

def test_easy_agent():
    state = GameState()
    agent = EasyAgent(player_id=Color.RED)
    move = agent.select_move(state)
    assert move is not None
    print(f"EasyAgent decided: {move}")

def test_medium_agent():
    state = GameState()
    agent = MediumAgent(player_id=Color.RED)
    move = agent.select_move(state)
    assert move is not None
    print(f"MediumAgent decided: {move}")

def test_hard_agent():
    state = GameState()
    agent = HardAgent(player_id=Color.RED)
    move = agent.select_move(state)
    assert move is not None
    print(f"HardAgent decided: {move}")

def test_agent_consistency():
    state = GameState()
    # Kiểm tra xem các agent có thực thị select_move hợp lệ từ state không
    agent1 = EasyAgent(player_id=Color.RED)
    agent2 = MediumAgent(player_id=Color.RED)
    agent3 = HardAgent(player_id=Color.RED)
    
    assert agent1.select_move(state.clone()) is not None
    assert agent2.select_move(state.clone()) is not None
    assert agent3.select_move(state.clone()) is not None

if __name__ == "__main__":
    print("--- Running test_easy_agent ---")
    test_easy_agent()
    
    print("\n--- Running test_medium_agent ---")
    test_medium_agent()
    
    print("\n--- Running test_hard_agent ---")
    test_hard_agent()
    
    print("\n--- Running test_agent_consistency ---")
    test_agent_consistency()
    
    print("\nAll tests passed!")
