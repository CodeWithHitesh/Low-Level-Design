"""Snake and Food Game implementation."""

from abc import ABC, abstractmethod
from collections import deque
from enum import Enum
from math import ceil
from random import randint
from typing import Deque, List, Tuple


# ─── Enums ────────────────────────────────────────────────────

class CellValues(Enum):
    EMPTY = 'EMPTY'
    FRUIT = 'FRUIT'
    SNAKE = 'SNAKE'


class Direction(Enum):
    UP = [-1, 0]
    DOWN = [1, 0]
    RIGHT = [0, 1]
    LEFT = [0, -1]


class GameState(Enum):
    IN_PROGRESS = 'IN_PROGRESS'
    GAME_OVER = 'GAME_OVER'


# ─── Template Method Pattern (Snake Movement) ─────────────────

class MoveSnake(ABC):
    """Template: prepend new head, then delegate tail handling to subclass."""

    def move(self, snake: Deque, pos_x: int, pos_y: int,
             board: List[List[CellValues]]) -> Tuple[Deque, List[List[CellValues]]]:
        snake.appendleft([pos_x, pos_y])
        board[pos_x][pos_y] = CellValues.SNAKE
        return self._move(snake, board)

    @abstractmethod
    def _move(self, snake: Deque, board: List[List[CellValues]]) -> Tuple[Deque, List[List[CellValues]]]:
        pass


class MoveSnakeFruit(MoveSnake):
    """Ate a fruit — keep the tail (snake grows)."""

    def _move(self, snake: Deque, board: List[List[CellValues]]) -> Tuple[Deque, List[List[CellValues]]]:
        return snake, board


class MoveSnakeEmpty(MoveSnake):
    """Moved to empty cell — remove tail (snake stays same length)."""

    def _move(self, snake: Deque, board: List[List[CellValues]]) -> Tuple[Deque, List[List[CellValues]]]:
        last_x, last_y = snake.pop()
        board[last_x][last_y] = CellValues.EMPTY
        return snake, board


# ─── Board ────────────────────────────────────────────────────

class Board:
    """Manages the grid, snake body, and fruit spawning."""

    def __init__(self, n_row: int, n_col: int, snake_len: int = 1, n_fruits: int = 0):
        self.grid: List[List[CellValues]] = [
            [CellValues.EMPTY for _ in range(n_col)] for _ in range(n_row)
        ]
        self.snake: Deque = deque()
        self._initSnake(snake_len, n_row, n_col)
        self._initFruits(n_fruits, n_row, n_col)

    def _initFruits(self, n_fruits: int, n_row: int, n_col: int) -> None:
        if not n_fruits:
            n_fruits = ceil((n_col * n_row) / 5)

        while n_fruits:
            rand_i, rand_j = randint(0, n_row - 1), randint(0, n_col - 1)
            if self.grid[rand_i][rand_j] == CellValues.EMPTY:
                self.grid[rand_i][rand_j] = CellValues.FRUIT
                n_fruits -= 1

    def spawnNewFruit(self) -> None:
        n_row, n_col = len(self.grid), len(self.grid[0])

        has_empty = any(
            self.grid[i][j] == CellValues.EMPTY
            for i in range(n_row) for j in range(n_col)
        )
        if not has_empty:
            return

        while True:
            rand_i, rand_j = randint(0, n_row - 1), randint(0, n_col - 1)
            if self.grid[rand_i][rand_j] == CellValues.EMPTY:
                self.grid[rand_i][rand_j] = CellValues.FRUIT
                return

    def _initSnake(self, snake_len: int, n_row: int, n_col: int) -> None:
        self.snake.append([n_row // 2, n_col // 2])
        self.grid[n_row // 2][n_col // 2] = CellValues.SNAKE

        for _ in range(snake_len - 1):
            last_pos = self.snake[-1]
            new_pos = [last_pos[0], (last_pos[1] + 1) % len(self.grid[0])]
            self.snake.append(new_pos)
            self.grid[new_pos[0]][new_pos[1]] = CellValues.SNAKE

    def getSnake(self) -> Deque:
        return self.snake

    def getGrid(self) -> List[List[CellValues]]:
        return self.grid

    def moveSnake(self, new_head_x: int, new_head_y: int,
                  cell_value: CellValues) -> Tuple[Deque, List[List[CellValues]]]:
        """Move the snake using the appropriate strategy based on cell type."""
        strategy = {
            CellValues.EMPTY: MoveSnakeEmpty(),
            CellValues.FRUIT: MoveSnakeFruit(),
        }
        self.snake, self.grid = strategy.get(cell_value).move(
            self.snake, new_head_x, new_head_y, self.grid
        )
        if cell_value == CellValues.FRUIT:
            self.spawnNewFruit()
        return self.snake, self.grid

    def display(self) -> None:
        print("\nCurrent board state:\n")
        for row in self.grid:
            print(" ".join(cell.value[0] for cell in row))
        print()


# ─── Strategy Pattern (Player Input) ─────────────────────────

class PlayerStrategy(ABC):
    @abstractmethod
    def makeMove(self, board: Board) -> List[int]:
        pass


class HumanPlayerStrategy(PlayerStrategy):
    def makeMove(self, board: Board) -> List[int]:
        while True:
            choice = input("Enter direction (UP, DOWN, RIGHT, LEFT): ").upper()
            try:
                return Direction[choice].value
            except KeyError:
                print("Please enter a valid direction!")


class Player:
    """A player that delegates move decisions to a strategy."""

    def __init__(self, name: str, strategy: PlayerStrategy):
        self.name = name
        self.strategy = strategy

    def makeMove(self, board: Board) -> List[int]:
        return self.strategy.makeMove(board)


# ─── Factory ──────────────────────────────────────────────────

class PlayerFactory:
    """Creates players with the appropriate input strategy."""

    @staticmethod
    def create(name: str, player_type: str) -> Player:
        strategies = {
            'human': HumanPlayerStrategy(),
        }
        strategy = strategies.get(player_type.lower(), HumanPlayerStrategy())
        return Player(name, strategy)


# ─── Game Orchestrator ────────────────────────────────────────

class Game:
    """Main game loop: reads input, updates board, checks game-over conditions."""

    def __init__(self, player_name: str, player_type: str,
                 n_row: int, n_col: int, snake_len: int, n_fruits: int):
        self.player = PlayerFactory.create(player_name, player_type)
        self.board = Board(n_row, n_col, snake_len, n_fruits)
        self.curr_state = GameState.IN_PROGRESS
        self.snake = self.board.getSnake()
        self.grid = self.board.getGrid()

    def play(self) -> None:
        while self.curr_state == GameState.IN_PROGRESS:
            dir_x, dir_y = self.player.makeMove(self.board)

            head_x, head_y = self.snake[0]
            new_head_x = dir_x + head_x
            new_head_y = (dir_y + head_y) % len(self.grid[0])

            if not (0 <= new_head_x < len(self.grid)):
                self.curr_state = GameState.GAME_OVER
                print("Game Over! Hit Vertical Boundary!")

            elif (self.grid[new_head_x][new_head_y] == CellValues.SNAKE
                  and [new_head_x, new_head_y] != self.snake[-1]):
                self.curr_state = GameState.GAME_OVER
                print("Game Over! Hit Itself!")

            elif self.grid[new_head_x][new_head_y] == CellValues.FRUIT:
                self.snake, self.grid = self.board.moveSnake(new_head_x, new_head_y, CellValues.FRUIT)

            else:
                self.snake, self.grid = self.board.moveSnake(new_head_x, new_head_y, CellValues.EMPTY)

            self.board.display()


# ─── Demo ─────────────────────────────────────────────────────

if __name__ == "__main__":
    game = Game("Player1", "human", n_row=8, n_col=8, snake_len=3, n_fruits=5)
    game.play()