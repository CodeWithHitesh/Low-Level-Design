from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple


# --- Enums --------------------------------------------------------

class GameState(Enum):
    """Enum for game states."""
    IN_PROGRESS = 'in_progress'
    WHITE_WIN = 'white_win'
    BLACK_WIN = 'black_win'
    DRAW = 'draw'


# --- Abstract Base Classes ----------------------------------------

class Piece(ABC):
    """Abstract base class for all chess pieces (Template Method Pattern)."""

    def __init__(self, is_white: bool) -> None:
        self.is_white = is_white

    def canMove(self, board: 'Board', start: 'Cell', end: 'Cell') -> bool:
        """Validate move: reject self-capture, then delegate to subclass."""
        if end.piece and end.piece.is_white == self.is_white:
            return False
        return self._canMove(board, start, end)

    @abstractmethod
    def _canMove(self, board: 'Board', start: 'Cell', end: 'Cell') -> bool:
        """Template Method - subclasses implement specific movement rules."""
        pass


# --- Concrete Piece Implementations -------------------------------

class Rook(Piece):
    """Rook moves horizontally or vertically."""

    def _canMove(self, board: 'Board', start: 'Cell', end: 'Cell') -> bool:
        x_diff = abs(start.row - end.row)
        y_diff = abs(start.col - end.col)
        if x_diff != 0 and y_diff != 0:
            return False
        return self._pathClear(board, start, end)

    def _pathClear(self, board: 'Board', start: 'Cell', end: 'Cell') -> bool:
        """Check that no piece blocks the straight-line path."""
        if start.row == end.row:
            step = 1 if end.col > start.col else -1
            for col in range(start.col + step, end.col, step):
                if board.grid[start.row][col].piece is not None:
                    return False
        elif start.col == end.col:
            step = 1 if end.row > start.row else -1
            for row in range(start.row + step, end.row, step):
                if board.grid[row][start.col].piece is not None:
                    return False
        return True


class Knight(Piece):
    """Knight moves in an L-shape."""

    def _canMove(self, board: 'Board', start: 'Cell', end: 'Cell') -> bool:
        x_diff = abs(start.row - end.row)
        y_diff = abs(start.col - end.col)
        return x_diff * y_diff == 2


class Bishop(Piece):
    """Bishop moves diagonally."""

    def _canMove(self, board: 'Board', start: 'Cell', end: 'Cell') -> bool:
        x_diff = abs(start.row - end.row)
        y_diff = abs(start.col - end.col)
        if x_diff != y_diff:
            return False
        return self._pathClear(board, start, end)

    def _pathClear(self, board: 'Board', start: 'Cell', end: 'Cell') -> bool:
        """Check that no piece blocks the diagonal path."""
        row_step = 1 if start.row < end.row else -1
        col_step = 1 if start.col < end.col else -1
        row, col = start.row + row_step, start.col + col_step
        while row != end.row and col != end.col:
            if board.grid[row][col].piece is not None:
                return False
            row += row_step
            col += col_step
        return True


class King(Piece):
    """King moves one square in any direction."""

    def _canMove(self, board: 'Board', start: 'Cell', end: 'Cell') -> bool:
        x_diff = abs(start.row - end.row)
        y_diff = abs(start.col - end.col)
        return max(x_diff, y_diff) == 1


class Queen(Piece):
    """Queen combines Rook and Bishop movement."""

    def _canMove(self, board: 'Board', start: 'Cell', end: 'Cell') -> bool:
        return (Rook(self.is_white)._canMove(board, start, end) or
                Bishop(self.is_white)._canMove(board, start, end))


class Pawn(Piece):
    """Pawn moves forward, captures diagonally."""

    def _canMove(self, board: 'Board', start: 'Cell', end: 'Cell') -> bool:
        direction = -1 if self.is_white else 1

        if start.col == end.col and end.row - start.row == direction and end.piece is None:
            return True

        if (
            start.col == end.col and
            ((self.is_white and start.row == 6) or (not self.is_white and start.row == 1)) and
            end.row - start.row == 2 * direction and
            end.piece is None
        ):
            return True

        if abs(start.col - end.col) == 1 and end.row - start.row == direction and end.piece:
            return True

        # TODO: Add en passant, promotion
        return False


# --- Dataclass Models ---------------------------------------------

@dataclass
class Cell:
    """Represents a cell on the chess board, holding its position and the piece on it."""
    row: int
    col: int
    piece: Optional[Piece] = None

    def getPos(self) -> Tuple[int, int]:
        """Return (row, col) tuple."""
        return (self.row, self.col)


@dataclass
class Player:
    """Represents a chess player."""
    is_white: bool
    name: str
    # TODO: Add player strategy (Human vs AI) using Strategy Pattern


@dataclass
class Move:
    """Represents a chess move from one cell to another."""
    start: Cell
    end: Cell


# --- Factory ------------------------------------------------------

class PieceFactory:
    """Factory Pattern - Creates pieces based on type."""

    @staticmethod
    def create(piece_type: str, is_white: bool) -> Piece:
        """Create a Piece subclass instance by name."""
        pieces = {
            'rook': Rook, 'knight': Knight, 'bishop': Bishop,
            'king': King, 'queen': Queen, 'pawn': Pawn
        }
        piece_class = pieces.get(piece_type.lower())
        if not piece_class:
            raise ValueError(f"Invalid piece type: {piece_type}")
        return piece_class(is_white)


# --- Singleton Board ----------------------------------------------

class Board:
    """Singleton Pattern - Ensures single board instance."""
    _instance: Optional['Board'] = None

    def __new__(cls) -> 'Board':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self.grid: List[List[Cell]] = [[None] * 8 for _ in range(8)]
        self._initializeBoard()
        self._initialized = True

    def _initializeBoard(self) -> None:
        """Set up initial chess board configuration."""
        piece_order = ['rook', 'knight', 'bishop', 'queen', 'king', 'bishop', 'knight', 'rook']
        for col_idx in range(len(piece_order)):
            self.grid[0][col_idx] = Cell(0, col_idx, PieceFactory.create(piece_order[col_idx], False))
            self.grid[1][col_idx] = Cell(1, col_idx, PieceFactory.create('pawn', False))
        for col_idx in range(len(piece_order)):
            self.grid[7][col_idx] = Cell(7, col_idx, PieceFactory.create(piece_order[col_idx], True))
            self.grid[6][col_idx] = Cell(6, col_idx, PieceFactory.create('pawn', True))
        for row_idx in range(2, 6):
            for col_idx in range(8):
                self.grid[row_idx][col_idx] = Cell(row_idx, col_idx, None)

    @classmethod
    def getInstance(cls) -> 'Board':
        """Return the singleton Board instance."""
        return cls()


# --- Orchestrator -------------------------------------------------

class Game:
    """Main game controller - manages game state and rules."""

    def __init__(self) -> None:
        self.board = Board.getInstance()
        self.players = [Player(True, "White"), Player(False, "Black")]
        self.is_white_turn: bool = True
        self.current_state: GameState = GameState.IN_PROGRESS

    def isValidMove(self, move: Move) -> bool:
        """Validate move based on piece rules and game state."""
        if not move.start.piece:
            return False
        if move.start.piece.is_white != self.is_white_turn:
            return False
        return move.start.piece.canMove(self.board, move.start, move.end)
        # TODO: Add check/checkmate validation

    def makeMove(self, start_row: int, start_col: int, end_row: int, end_col: int) -> bool:
        """Execute a validated move."""
        if not all(0 <= x < 8 for x in [start_row, start_col, end_row, end_col]):
            return False

        start_cell = self.board.grid[start_row][start_col]
        end_cell = self.board.grid[end_row][end_col]
        move = Move(start_cell, end_cell)

        if self.isValidMove(move):
            if end_cell.piece and isinstance(end_cell.piece, King):
                self.current_state = GameState.WHITE_WIN if self.is_white_turn else GameState.BLACK_WIN

            end_cell.piece = start_cell.piece
            start_cell.piece = None
            self.is_white_turn = not self.is_white_turn
            return True
        return False

    def start(self, move_provider) -> None:
        """
        Starts the game loop. The move_provider function should return a tuple:
        (start_row, start_col, end_row, end_col)
        """
        while self.current_state == GameState.IN_PROGRESS:
            print(f"\n{'White' if self.is_white_turn else 'Black'}'s turn.")
            move = move_provider(self)
            if move is None:
                print("No move provided. Exiting game.")
                break
            start_row, start_col, end_row, end_col = move
            if not self.makeMove(start_row, start_col, end_row, end_col):
                print("Invalid move, try again.")
            else:
                print(f"Moved from ({start_row},{start_col}) to ({end_row},{end_col})")


# --- Demo ---------------------------------------------------------

if __name__ == "__main__":
    def consoleMoveProvider(game: Game) -> Optional[Tuple[int, int, int, int]]:
        try:
            move_str = input("Enter move as 'start_row start_col end_row end_col': ")
            return tuple(map(int, move_str.strip().split()))
        except Exception:
            print("Invalid input format.")
            return None

    def playChessGame() -> None:
        """Create a Game instance and start the chess game using console input."""
        game = Game()
        game.start(consoleMoveProvider)
        if game.current_state == GameState.WHITE_WIN:
            print("White wins!")
        elif game.current_state == GameState.BLACK_WIN:
            print("Black wins!")
        elif game.current_state == GameState.DRAW:
            print("Game is a draw.")
        else:
            print("Game ended.")

    playChessGame()

# TODO: Add move history with Memento pattern
# TODO: Add Observer pattern for game events/notifications
# TODO: Add undo/redo functionality
# TODO: Add checkmate detection
# TODO: Add stalemate detection
