from enum import Enum
from abc import ABC, abstractmethod
from typing import Tuple, List, Optional


"""Tic-Tac-Toe LLD module.

Contains Strategy-based players, a Board, Observer interfaces, a PlayerFactory,
and a Game controller. Code formatted and docstrings added for interview
readability and maintainability.
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
        """
        Return a tuple (row, col) for the next move given the board.

        Args:
            board: Board instance used to decide the move.

        Returns:
            (row, col) indices for the chosen move.
        """
        pass


class HumanPlayerStrategy(PlayerStrategy):
    """Human strategy that reads integers from stdin."""
    
    def make_move(self, board) -> Tuple[int, int]:
        """
        Prompt the user for a row and column until a valid move is provided.

        Args:
            board: Board instance to validate moves against.

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


# Factory Design Pattern for creating different player types
class PlayerFactory:
    """Simple factory to create different kinds of Player objects."""

    @staticmethod
    def create_player(player_type: str, name: str, symbol: Symbol) -> Player:
        """
        Create a Player based on the requested type.

        Args:
            player_type: 'human' (default) or future AI types.
            name: Player display name.
            symbol: Symbol assigned to the player.

        Returns:
            Player instance.
        """
        strategies = {
            'human': HumanPlayerStrategy(),
            # 'random_ai': RandomAIStrategy(),  # add AI strategies as needed
        }
        strategy = strategies.get(player_type, HumanPlayerStrategy())
        return Player(name, symbol, strategy)


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

        Args:
            row: Row index.
            col: Column index.
            symbol: Symbol to place.
        
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

    def display(self) -> None:
        """Print the current board to stdout in a human-readable format."""
        for row in self.grid:
            print( '|'.join(cell.value for cell in row))
            print( '-' * (self.size * 2 - 1) )


class State(Enum):
    """High level game states."""
    IN_PROGRESS = 'In Progress'
    X_WIN = 'X Win'
    O_WIN = 'O Win'
    DRAW = 'Draw'


# Observer Pattern
class GameObserver(ABC):
    """Observer interface for game events."""

    @abstractmethod
    def on_move_made(self, player: Player, row: int, col: int) -> None:
        """Called when a move is successfully made."""
        pass

    @abstractmethod
    def on_game_state_changed(self, state: State, winner: Optional[Player]) -> None:
        """Called when the game state changes (win/draw)."""
        pass


class ConsoleDisplayObserver(GameObserver):
    """Console observer that prints basic notifications to stdout."""
    def on_move_made(self, player: Player, row: int, col: int) -> None:
        """Print the move that was made."""
        print(f"{player.name} placed {player.symbol.value} at ({row}, {col})")

    def on_game_state_changed(self, state: State, winner: Optional[Player] = None) -> None:
        """Print the final game state."""
        if state == State.DRAW:
            print("Game ended in a draw")
        else:
            print(f"{winner.name} ({winner.symbol.value}) wins the game")


class Game:
    """Main game controller responsible for turn flow and state transitions."""

    def __init__(self, size: int = 3):
        """
        Initialize a Game.

        Args:
            size: Board size (size x size).
            players: Optional list of two Player instances. If None, two human players are created.
        """
        self.size = size
        self.players = [
                PlayerFactory.create_player('human', 'Player 1', Symbol.X),
                PlayerFactory.create_player('human', 'Player 2', Symbol.O),
        ]
        self.board = Board(self.size)
        self.current_turn = 0
        self.current_symbol = self.players[0].symbol
        self.current_state = State.IN_PROGRESS
        self.remaining_cells = self.size * self.size
        self.observers: List[GameObserver] = []

    def register_observer(self, observer: GameObserver) -> None:
        """Register an observer to receive game events."""
        self.observers.append(observer)

    def notify_move(self, player: Player, row: int, col: int) -> None:
        """Notify observers that a move was made."""
        for observer in self.observers:
            observer.on_move_made(player, row, col)

    def notify_game_state_changed(self, state: State, winner: Optional[Player] = None) -> None:
        """Notify observers that the game state changed."""
        for observer in self.observers:
            observer.on_game_state_changed(state, winner)

    def play(self) -> None:
        """
        Main play loop.

        - Requests a valid move from the current player's strategy.
        - Applies the move only if valid.
        - Updates remaining cell count, checks for win/draw, notifies observers, and switches turns.
        """
        while self.current_state == State.IN_PROGRESS:
            player = self.players[self.current_turn]
            row, col = player.make_move(self.board)

            self.board.mark_cell(row, col, player.symbol)

            self.remaining_cells -= 1
            self.notify_move(player, row, col)
            self.board.display()

            # Check for a winner
            if self.board.check_winner(player.symbol):
                self.current_state = State.X_WIN if player.symbol == Symbol.X else State.O_WIN
                self.notify_game_state_changed(self.current_state, player)
                break

            # Check for draw
            if self.remaining_cells == 0:
                self.current_state = State.DRAW
                self.notify_game_state_changed(self.current_state, None)
                break

            # Switch turn
            self.current_turn ^= 1
            self.current_symbol = self.players[self.current_turn].symbol

    def reset_game(self) -> None:
        """Reset board and game status while preserving observers and players."""
        self.board = Board(self.size)
        self.current_turn = 0
        self.current_symbol = self.players[0].symbol
        self.current_state = State.IN_PROGRESS
        self.remaining_cells = self.size * self.size


if __name__ == "__main__":
    game = Game()
    game.register_observer(ConsoleDisplayObserver())
    game.play()