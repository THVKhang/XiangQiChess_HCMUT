# Artificial Intelligence Engine: Algorithmic Architecture and Difficulty Scaling

## 1. Algorithmic Foundation

The decision-making core of the Xiangqi Artificial Intelligence relies on game-tree search algorithms. To accommodate a scalable computational framework, the system implements a duality of search paradigms:

### 1.1. Minimax Algorithm
As a baseline for zero-sum game theory, the classical Minimax algorithm simulates the game tree by assuming optimal play from both sides. It recursively evaluates subsequent game states, maximizing the current player's utility while minimizing the opponent's. Although theoretically sound, the pure Minimax implementation suffers from exponential time complexity $O(b^d)$ (where $b$ is the branching factor and $d$ is the search depth), making it computationally prohibitive for deeper evaluations in a complex domain like Xiangqi.

### 1.2. Alpha-Beta Pruning
To mitigate the exponential explosion of the game tree, the Alpha-Beta pruning algorithm is strategically employed as the primary search engine. By maintaining two bounding variables—$\alpha$ (the minimum score the maximizing player is assured of) and $\beta$ (the maximum score the minimizing player is assured of)—the algorithm mathematically eliminates subordinate branches that cannot possibly influence the final decision. In the theoretical optimum, Alpha-Beta pruning reduces the time complexity to $O(b^{d/2})$, exponentially expanding the feasible search depth within identical temporal constraints.

## 2. Advanced Search Optimizations

To further enhance the efficiency of the Alpha-Beta search and achieve lower latency in real-time execution, several sophisticated optimization techniques have been integrated.

### 2.1. Heuristic Move Ordering (MVV-LVA)
The efficacy of Alpha-Beta pruning is heavily dependent on the order in which nodes are evaluated. If potentially optimal moves are evaluated earlier, larger sections of the tree can be instantaneously pruned. The engine incorporates a heuristic **Move Ordering** mechanism utilizing the **Most Valuable Victim - Least Valuable Attacker (MVV-LVA)** principle. By prioritizing captures where a high-value piece is attacked by a low-value piece, the engine aggressively forces early cutoffs in the search tree.

### 2.2. Transposition Tables
In Xiangqi, highly disparate sequences of moves can frequently converge into identical board configurations (transpositions). To prevent redundant computational overhead, the engine integrates a **Transposition Table** architecture. Each unique board state is mathematically serialized into an immutable hash equivalent (in Python, utilizing highly optimized `frozenset` operations mapping piece coordinates, types, and affiliations). When encountering a previously evaluated state, the engine retrospectively retrieves the exact score or the relevant $\alpha/\beta$ bounds, effectively truncating redundant subtree explorations.

### 2.3. Heuristic Evaluation Caching
Symmetric to transposition tables, **Evaluation Caching** creates a memorization dictionary specifically for terminal node static evaluations. Due to the high frequency of identical terminal states appearing across different search branches, caching the computationally expensive positional heuristics drastically reduces redundant iterations over the board state.

## 3. Static Evaluation Heuristics

The leaf nodes of the search tree are quantified utilizing static evaluation functions. The agent transitions between two heuristic modalities dynamically based on its configured cognitive capacity.

### 3.1. Material-Centric Evaluation (Basic)
The fundamental heuristic linearly aggregates the intrinsic material value of each active piece. The deterministic piece values are empirically derived: General (10,000), Rook (900), Cannon (450), Knight (400), Elephant/Advisor (200), and Pawn (100). This provides a foundational quantitative metric for material superiority.

### 3.2. Positional and Strategic Evaluation (Advanced)
A more sophisticated heuristic function augments the basic material count with spatial and tactical significance:
* **Pawn Advancement:** Rewards exponential value to Pawns successfully crossing the river, particularly those approaching the opponent's inner palace (Nine-Palace).
* **Piece Mobility & Deployment:** Penalizes Edge Knights (due to restricted mobility) whilst rewarding Central Knights. Rooks are incentivized to control centralized and critical files.
* **Palace Defense Coordination:** Evaluates the structural integrity of the defensive posture. Generals departing the central file, or dismantled Advisor/Elephant formations, incur significant detrimental scores.

## 4. Difficulty Stratification Matrix (Levels 1 - 10)

The cognitive prowess of the AI is strictly modulated across ten distinct difficulty tiers. This is achieved through a multi-dimensional configuration encompassing search depth, heuristic complexity, and optimization constraints.

| Level | Classification | Search Depth | Heuristic Topology | Move Ordering (MVV-LVA) |
| :---: | :--- | :---: | :--- | :---: |
| **1** | Beginner | $d = 1$ | Basic (Material) | Disabled |
| **2** | Novice | $d = 1$ | Advanced (Positional) | Disabled |
| **3** | Intermediate | $d = 2$ | Basic (Material) | Disabled |
| **4** | Competent | $d = 2$ | Advanced (Positional) | Disabled |
| **5** | Advanced | $d = 2$ | Advanced (Positional) | Enabled |
| **6** | Expert | $d = 3$ | Basic (Material) | Disabled |
| **7** | Master | $d = 3$ | Advanced (Positional) | Disabled |
| **8** | Grandmaster | $d = 3$ | Advanced (Positional) | Enabled |
| **9** | Elite | $d = 4$ | Advanced (Positional) | Disabled |
| **10**| State-of-the-Art| $d = 4$ | Advanced (Positional) | Enabled |

Through this rigorously parameterized matrix, the artificial intelligence ensures a pedagogically progressive adversary, ranging from instantaneous, purely reactive play (Level 1) to highly strategic, deeply calculative configurations (Level 10).
