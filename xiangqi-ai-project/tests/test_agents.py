from core.state import GameState
from core.rules import Color
from agents.search_agent import EasyAgent, MediumAgent, HardAgent, LevelAgent

def test_easy_agent(algo="alphabeta"):
    state = GameState()
    agent = EasyAgent(player_id=Color.RED, algorithm=algo)
    move = agent.select_move(state)
    assert move is not None
    print(f"EasyAgent decided: {move}")

def test_medium_agent(algo="alphabeta"):
    state = GameState()
    agent = MediumAgent(player_id=Color.RED, algorithm=algo)
    move = agent.select_move(state)
    assert move is not None
    print(f"MediumAgent decided: {move}")

def test_hard_agent(algo="alphabeta"):
    state = GameState()
    agent = HardAgent(player_id=Color.RED, algorithm=algo)
    move = agent.select_move(state)
    assert move is not None
    print(f"HardAgent decided: {move}")

def test_agent_consistency(algo="alphabeta"):
    state = GameState()
    # Kiểm tra xem các agent có thực thị select_move hợp lệ từ state không
    agent1 = EasyAgent(player_id=Color.RED, algorithm=algo)
    agent2 = MediumAgent(player_id=Color.RED, algorithm=algo)
    agent3 = HardAgent(player_id=Color.RED, algorithm=algo)
    
    assert agent1.select_move(state.clone()) is not None
    assert agent2.select_move(state.clone()) is not None
    assert agent3.select_move(state.clone()) is not None

def test_level_agent(n=1, algo="alphabeta"):
    state = GameState()
    print("\n[Testing LevelAgent Custom]")
    
    agent = LevelAgent(player_id=Color.RED, algorithm=algo, level=n)
    move = agent.select_move(state.clone())
    assert move is not None
    print(f"LevelAgent (Level {n}) decided: {move}")

if __name__ == "__main__":
    algo = input("Enter algorithm (minimax/alphabeta): ")

    print("--- Running test_easy_agent ---")
    test_easy_agent(algo)
    
    print("\n--- Running test_medium_agent ---")
    test_medium_agent(algo)
    
    print("\n--- Running test_hard_agent ---")
    test_hard_agent(algo)
    
    print("\n--- Running test_agent_consistency ---")
    test_agent_consistency()
    
    print("\n--- Running test_level_agent ---")
    n = int(input("Enter level: "))
    test_level_agent(n, algo)
    
    print("\nAll tests passed!")
