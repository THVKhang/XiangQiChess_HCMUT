# Artificial Intelligence Subsystem: Architectural Design and Abstractions

## 1. Architectural Overview

The Artificial Intelligence (AI) subsystem of the Xiangqi engine is architected around principles of object-oriented design, specifically leveraging the **Strategy Design Pattern** and **Polymorphism**. This structural decision decouples the core game logic (move generation, board state management, and rule enforcement) from the decision-making heuristics, enabling the seamless interchangeability and scalable evolution of computational agents.

The core of this architecture is the `BaseAgent` abstract class, which establishes a generalized contractual interface for any entity interacting with the game matrix. By encapsulating the decision algorithm within derived subclasses that implement the homogeneous `select_move(GameState)` method, the system achieves strict separation of concerns and high modularity.

## 2. Abstract Interface (`BaseAgent`)

The underlying foundation of the adversarial network is the `BaseAgent`, which functions as an abstract base class. It defines the minimal systemic footprint required for an agent to participate in the simulation:

* **Identity Management:** Aggregates inherent properties such as `player_id` (Red/Black faction affiliation) and semantic nomenclature (`name`).
* **Decisional Contract:** Imposes the `select_move(state: GameState) -> Optional[Move]` abstract method constraint. The invocation of this function prompts the specific agent to analyze the encapsulated board state and mathematically yield an optimal (or stochastic) action vector.

## 3. Concrete Agent Implementations (Strategy Polymorphism)

The subsystem integrates an expandable polymorphic hierarchy of concrete agents, each mapped to distinctly divergent behavioral and computational models.

### 3.1. Stochastic Baseline (`RandomAgent`)
The `RandomAgent` establishes the algorithmic lower bound of the application. By querying the legal move space and selecting a transition exclusively via a mathematically uniform random probability distribution, it serves both as an elementary baseline for algorithm validation (e.g., stochastic play-outs) and a trivial benchmark to measure heuristic improvements against.

### 3.2. User Interface Proxy (`HumanPlayer`)
The systemic architectural symmetry is preserved for organic entities via the `HumanPlayer` proxy class. Rather than processing heuristic search trees, this entity suspends the execution thread to await asynchronous external input (via terminal or potentially a graphical user interface). It formally wraps standard human operations into the codified `Move` object topology to satisfy the `select_move` execution contract.

### 3.3. Deterministic Search Entities (`MinimaxAgent` & `AlphaBetaAgent`)
These agents encapsulate the cognitive intelligence engine of the application:
* **MinimaxAgent:** Implements the pure, unadulterated Minimax decision rule. Serving primarily as a pedagogical referent and comparative baseline, it recursively traverses the theoretical game tree without early termination logic.
* **AlphaBetaAgent:** Inherently expands upon Minimax by introducing mathematically rigorous alpha-beta pruning bounds. It serves as the primary intelligence orchestrator, incorporating computationally sophisticated mechanics (e.g., MVV-LVA move ordering criteria, state transition caching) to significantly compress the effective branching factor, thereby optimizing the temporal complexities of deep searches.

## 4. Scalable Cognitive Modeling (`LevelAgent`)

To construct a pedagogically viable hierarchy of adversarial difficulty, the `LevelAgent` operates as a parameterized configuration class extending the `AlphaBetaAgent`. It relies on a pre-computed stratification matrix (`get_level_config`) to deterministically modulate three primary cognitive dimensions based on an integer input (1-10):

1. **Analytical Horizon (Search Depth):** Binds the maximum recursion depth, scaling dynamically across varying plies.
2. **Heuristic Granularity:** Switches categorically between simplistic sub-routines (linear material-counting) and advanced tensor-like positional-strategic evaluation criteria.
3. **Optimizations Pipeline:** Selectively enables advanced pruning heuristics like Move Ordering only at subsequent threshold complexities to simulate suboptimal cognitive processing at lower tiers.

Through this parameterization, the `LevelAgent` simulates an organic progression in computational competence. Static subclass derivations such as `EasyAgent`, `MediumAgent`, and `HardAgent` function as convenient instantiation aliases for standardized difficulty brackets.

## 5. Architectural Orthogonality and Extensibility
By strictly adhering to abstract coupling, the AI architecture remains entirely orthogonal to the engine ruleset. Future structural integrations of alternative methodologies—such as Probabilistic Monte Carlo Tree Search (MCTS), Evolutionary Algorithms, or Convolutional Neural Networks (e.g., AlphaZero-inspired architectures)—can be executed natively. This is accomplished simply by deriving a novel functional class from `BaseAgent` and overriding its `select_move` resolution algorithm, guaranteeing mathematical extensibility without necessitating retrospective modification of the existing implementation constraints.
