from enum import Enum
from abc import ABC, abstractmethod
from typing import Tuple


"""Tic-Tac-Toe LLD module.

Contains simple Strategy-based players, a Board, Game state enum, and a Game
controller. Code formatted and docstrings added for interview readability.
"""


class Symbol(Enum):
    """Symbol used on the board."""
    X = 'X'
    O = 'O'
    EMPTY = ' '


# Strategy Pattern for Player Moves
class PlayerStrategy(ABC):
    """Abstract strategy for selecting a move."""

    @abstractmethod
    def make_move(self, board) -> Tuple[int, int]:
        """Return (row, col) for the next move given the board."""
        pass


class HumanPlayerStrategy(PlayerStrategy):
    """Human strategy that reads integers from stdin."""

    def make_move(self, board) -> Tuple[int, int]:
        """
        Prompt the user for a row and column until a valid move is provided.

        Returns:
            Tuple[int, int]: (row, col) chosen by the user.
        """
        while True:
            try:
                row = int(input("Enter the row (0, 1, 2): "))
                col = int(input("Enter the column (0, 1, 2): "))
                if board.is_valid_move(row, col):
                    return row, col
                print("Invalid move. Try again.")
            except ValueError:
                print("Please enter valid integers for row and column.")


class Player:
    """Represents a player with a name, symbol and move strategy."""

    def __init__(self, name: str, symbol: Symbol, strategy: PlayerStrategy):
        """
        Initialize a player.

        Args:
            name: Player's display name.
            symbol: Symbol used on the board (Symbol.X or Symbol.O).
            strategy: Strategy used to select moves.
        """
        self.name = name
        self.symbol = symbol
        self.strategy = strategy

    def make_move(self, board) -> Tuple[int, int]:
        """Delegate move selection to the player's strategy."""
        return self.strategy.make_move(board)


class Board:
    """Represents the game board."""

    def __init__(self, size: int = 3):
        """
        Initialize the board.

        Args:
            size: Board dimension (size x size). Default is 3.
        """
        self.size = size
        self.grid = [[Symbol.EMPTY for _ in range(size)] for _ in range(size)]

    def is_valid_move(self, row: int, col: int) -> bool:
        """Return True if the given cell is within bounds and empty."""
        return 0 <= row < self.size and 0 <= col < self.size and self.grid[row][col] == Symbol.EMPTY

    def mark_cell(self, row: int, col: int, symbol: Symbol) -> bool:
        """
        Mark a cell with the given symbol if valid.

        Returns:
            True if the cell was marked, False if the move was invalid.
        """
        if self.is_valid_move(row, col):
            self.grid[row][col] = symbol
            return True
        return False

    def check_winner(self, symbol: Symbol) -> bool:
        """
        Check whether the given symbol has a winning line.

        Returns:
            True if symbol has a complete row, column or diagonal.
        """
        # rows
        for row in self.grid:
            if all(cell == symbol for cell in row):
                return True

        # columns
        for col in range(self.size):
            if all(self.grid[row][col] == symbol for row in range(self.size)):
                return True

        # diagonals
        if all(self.grid[i][i] == symbol for i in range(self.size)):
            return True
        if all(self.grid[i][self.size - 1 - i] == symbol for i in range(self.size)):
            return True

        return False

class State(Enum):
    """High level game states."""
    IN_PROGRESS = 'In Progress'
    X_WIN = 'X Win'
    O_WIN = 'O Win'
    DRAW = 'Draw'


class Game:
    """Main game controller responsible for turn flow and state transitions."""

    def __init__(self):
        self.players = [
            Player('Player 1', Symbol.X, HumanPlayerStrategy()),
            Player('Player 2', Symbol.O, HumanPlayerStrategy())
        ]
        self.size = 3
        self.board = Board(self.size)
        self.current_turn = 0
        self.current_symbol = Symbol.X
        self.current_state = State.IN_PROGRESS
        self.remaining_cells = self.size * self.size

    def play(self) -> None:
        """
        Main play loop.

        - Requests a valid move from the current player's strategy.
        - Updates remaining cell count, checks for win/draw, and switches turns.
        """
        while self.current_state == State.IN_PROGRESS:
            row, col = self.players[self.current_turn].make_move(self.board)
            self.board.mark_cell(row, col, self.current_symbol)
            self.remaining_cells -= 1

            if self.board.check_winner(self.current_symbol):
                self.current_state = State.X_WIN if self.current_symbol == Symbol.X else State.O_WIN
                print(f"{self.players[self.current_turn].name} ({self.current_symbol.value}) wins!")
                break

            if self.remaining_cells == 0:
                self.current_state = State.DRAW
                print("Game is a draw.")
                break

            # switch turn and symbol
            self.current_turn ^= 1
            self.current_symbol = Symbol.X if self.current_symbol == Symbol.O else Symbol.O
