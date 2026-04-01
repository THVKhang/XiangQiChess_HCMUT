# Report Outline: Algorithmic Engine and Difficulty Stratification

## 1. Algorithmic Framework and Search Mechanisms

### 1.1. Minimax Algorithm with Alpha-Beta Pruning
The core decision-making engine of the autonomous agent is predicated upon the **Minimax algorithm**, a deterministic adversarial search paradigm. To address the combinatorial explosion inherent in the game tree of Xiangqi, **Alpha-Beta pruning** is intrinsically applied. This optimization mathematically guarantees the elimination of sub-optimal game tree branches, thereby drastically accelerating the search process without compromising the integrity of the terminal decision. The dynamically pruned search tree facilitates deeper computational foresight within identical temporal constraints.

### 1.2. State Space Complexity Reduction
Given the vast state space complexity of Xiangqi (average branching factor $b \approx 38$), advanced state-caching methodologies have been implemented to optimize temporal performance:
*   **Zobrist Hashing and Transposition Tables**: A mathematically robust stochastic hashing mechanism (Zobrist Hashing) is utilized to generate near-unique 64-bit cryptographic representations of arbitrary board configurations. These hash identifiers index a Transposition Table, which caches previously calculated state evaluations, traversed search depths, and alpha-beta bounds. When identical topological board states are reached via heterogeneous move permutations (transpositions), the agent retrieves the cached metadata, thereby comprehensively circumventing redundant deterministic sub-tree expansions.
*   **Heuristic Evaluation Caching**: The static terminal-node evaluation function is a computationally intensive procedure. By implementing an auxiliary caching paradigm specifically dedicated to heuristic state-evaluations, the system significantly amortizes the computational overhead, directly reducing the inference latency during deep-tree traversals.

### 1.3. Static Evaluation Heuristics
The heuristic evaluation function serves as the quantitative oracle for non-terminal leaf nodes, computing a linear combination of localized tactical and strategic features. The foundational framework heavily weights the **Material Advantage Heuristic**, strategically allocating normalized numerical coefficients to distinct piece classes (e.g., Chariots, Cannons, Horses) to mathematically approximate the overarching positional and material advantage.

---

## 2. Difficulty Stratification and Performance Scaling

The cognitive complexity and tactical proficiency of the agent are dynamically regulated through a multi-tiered difficulty architecture, implicitly governed by constraints on algorithmic search depth and heuristic utilization:

### 2.1. Level 1: Novice (Depth 1 - 2)
Characterized by a severely truncated search horizon. The agent processes predominantly immediate tactical exchanges (e.g., capturing unilaterally exposed pieces) and lacks substantive strategic foresight. This configuration evaluates purely on shallow state transitions, generating an accessible, highly reactive opponent suitable for inexperienced human players.

### 2.2. Level 2: Intermediate (Depth 3 - 4)
The search horizon is expanded to permit fundamental combinatorial tactics and intermediate positional planning. While Alpha-Beta pruning is continuously active, the bounded traversal depth constrains the agent's capacity to foresee complex, multi-stage forcing sequences. The agent simulates moderate intellectual gameplay, balancing reasonable algorithmic execution time with adequate tactical defense and recognizable strategic patterns.

### 2.3. Level 3: Advanced / Expert (Depth 5+)
This tier represents the theoretical apex of the underlying algorithmic architecture. The search depth is maximized, comprehensively leveraging the Transposition Table and Zobrist Hashing to dynamically traverse extensive branches of the game tree. The agent consistently evaluates profound positional sacrifices, executes deep forcing sequences, and exhibits optimal strategic continuity. Computational resources are fully deployed to maximize the formulation of the objective function against complex adversarial strategies.
