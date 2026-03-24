import sys
import os
import time

# Đảm bảo có thể import các module từ thư mục cha
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.search_agent import EasyAgent, MediumAgent, HardAgent, LevelAgent
from core.state import GameState
from core.rules import Color

def benchmark_agent(agent, name, state, num_runs=3):
    print(f"\nBenchmarking [{name}] ({num_runs} lần)...")
    
    start_time = time.time()
    for _ in range(num_runs):
        move = agent.select_move(state.clone())
    end_time = time.time()
    
    avg_time = (end_time - start_time) / num_runs
    print(f"[{name}] Nước đi chọn: {move}")
    print(f"[{name}] Thời gian trung bình: {avg_time:.4f}s / nước đi")

if __name__ == "__main__":
    print("=== TẠO BÀN CỜ ĐỂ BENCHMARK TỐC ĐỘ AI ===")
    state = GameState()
    
    benchmark_agent(EasyAgent(player_id=Color.RED), "EasyAgent (Level 1 - Depth 1)", state, num_runs=10)
    
    benchmark_agent(MediumAgent(player_id=Color.RED), "MediumAgent (Level 4 - Depth 2)", state, num_runs=3)
    
    print("\nLưu ý: HardAgent (Depth 3) sẽ tốn thời gian hơn đáng kể...")
    benchmark_agent(HardAgent(player_id=Color.RED), "HardAgent (Level 8 - Depth 3 + Move Ordering)", state, num_runs=1)
    
    print("\nLưu ý: Thử nghiệm MasterAgent (Depth 4 + MVV-LVA)... cực kỳ chậm!")
    benchmark_agent(LevelAgent(player_id=Color.RED, level=10), "MasterAgent (Level 10 - Depth 4)", state, num_runs=1)
    
    print("\n=== BENCHMARK HOÀN TẤT ===")
