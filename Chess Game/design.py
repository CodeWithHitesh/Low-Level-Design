from abc import ABC, abstractmethod
from enum import Enum

class Cell:
    """
    Represents a cell on the chess board, holding its position and the piece on it.
    """
    def __init__(self, row, col, piece):
        self.row = row
        self.col = col
        self.piece = piece

    def get_pos(self):
        return [self.row, self.col]

class Piece(ABC):
    """
    Abstract base class for all chess pieces.
    """
    def __init__(self, is_white):
        self.is_white = is_white
        self.is_killed = False

    def can_move(self, board, start, end):
        end_piece = end.piece
        if end_piece and end_piece.is_white == self.is_white:
            return False
        return self._can_move(board, start, end)

    @abstractmethod
    def _can_move(self, board, start, end):
        pass

class Rook(Piece):
    """
    Represents a rook chess piece.
    """
    def _can_move(self, board, start, end):
        x_diff = abs(start.get_pos()[0] - end.get_pos()[0])
        y_diff = abs(start.get_pos()[1] - end.get_pos()[1])
        if x_diff != 0 and y_diff != 0:
            return False
        return self._path_clear(board, start, end)

    def _path_clear(self, board, start, end):
        start_row, start_col = start.get_pos()
        end_row, end_col = end.get_pos()
        if start_row == end_row:
            step = 1 if end_col > start_col else -1
            for col in range(start_col + step, end_col, step):
                if board.board[start_row][col].piece is not None:
                    return False
        elif start_col == end_col:
            step = 1 if end_row > start_row else -1
            for row in range(start_row + step, end_row, step):
                if board.board[row][start_col].piece is not None:
                    return False
        return True

class Knight(Piece):
    """
    Represents a knight chess piece.
    """
    def _can_move(self, board, start, end):
        x_diff = abs(start.get_pos()[0] - end.get_pos()[0])
        y_diff = abs(start.get_pos()[1] - end.get_pos()[1])
        return x_diff * y_diff == 2

class Bishop(Piece):
    """
    Represents a bishop chess piece.
    """
    def _can_move(self, board, start, end):
        x_diff = abs(start.get_pos()[0] - end.get_pos()[0])
        y_diff = abs(start.get_pos()[1] - end.get_pos()[1])
        if x_diff != y_diff:
            return False
        return self._check_path_clear(board, start, end)

    def _check_path_clear(self, board, start, end):
        start_row, start_col = start.get_pos()
        end_row, end_col = end.get_pos()
        row_step = 1 if start_row < end_row else -1
        col_step = 1 if start_col < end_col else -1
        row, col = start_row + row_step, start_col + col_step
        while row != end_row and col != end_col:
            if board.board[row][col].piece is not None:
                return False
            row += row_step
            col += col_step
        return True

class King(Piece):
    """
    Represents a king chess piece.
    """
    def _can_move(self, board, start, end):
        x_diff = abs(start.get_pos()[0] - end.get_pos()[0])
        y_diff = abs(start.get_pos()[1] - end.get_pos()[1])
        return max(x_diff, y_diff) == 1

class Queen(Piece):
    """
    Represents a queen chess piece.
    """
    def _can_move(self, board, start, end):
        return Rook(self.is_white)._can_move(board, start, end) or Bishop(self.is_white)._can_move(board, start, end)

class Pawn(Piece):
    """
    Represents a pawn chess piece.
    """
    def _can_move(self, board, start, end):
        start_row, start_col = start.get_pos()
        end_row, end_col = end.get_pos()
        direction = -1 if self.is_white else 1

        # Move forward by 1
        if start_col == end_col and end_row - start_row == direction and end.piece is None:
            return True

        # Move forward by 2 from starting position
        if (
            start_col == end_col and
            ((self.is_white and start_row == 6) or (not self.is_white and start_row == 1)) and
            end_row - start_row == 2 * direction and
            end.piece is None
        ):
            return True

        # Capture diagonally
        if (
            abs(start_col - end_col) == 1 and
            end_row - start_row == direction and
            end.piece is not None and
            end.piece.is_white != self.is_white
        ):
            return True

        return False

class PieceFactory:
    """
    Factory class to create chess pieces based on type.
    """
    @classmethod
    def create(cls, piece_type, is_piece_white):
        piece_type_mp = {
            'rook': Rook,
            'knight': Knight,
            'bishop': Bishop,
            'king': King,
            'queen': Queen,
            'pawn': Pawn
        }
        piece_class = piece_type_mp.get(piece_type.lower())
        if piece_class:
            return piece_class(is_piece_white)
        else:
            raise Exception(f"Piece type invalid: {piece_type}")

class Board:
    """
    Represents the chess board and manages the placement of pieces.
    Implements the singleton pattern.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Board, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', False):
            return
        self.board = [[None] * 8 for _ in range(8)]
        self.initialize_board()
        self._initialized = True

    def initialize_board(self):
        piece_order = ['rook', 'knight', 'bishop', 'queen', 'king', 'bishop', 'knight', 'rook']
        for col_idx in range(len(piece_order)):
            self.board[0][col_idx] = Cell(0, col_idx, PieceFactory.create(piece_order[col_idx], False))
            self.board[1][col_idx] = Cell(1, col_idx, PieceFactory.create('pawn', False))
        for col_idx in range(len(piece_order)):
            self.board[7][col_idx] = Cell(7, col_idx, PieceFactory.create(piece_order[col_idx], True))
            self.board[6][col_idx] = Cell(6, col_idx, PieceFactory.create('pawn', True))
        for row_idx in range(2, 6):
            for col_idx in range(8):
                self.board[row_idx][col_idx] = Cell(row_idx, col_idx, None)

    @classmethod
    def get_instance(cls):
        return cls()

class Player:
    """
    Represents a player in the chess game.
    """
    def __init__(self, is_white, name):
        self.is_white = is_white
        self.name = name

class GameState(Enum):
    """
    Enum representing the possible states of the chess game.
    """
    IN_PROGRESS = 'in_progress'
    WHITE_WIN = 'white_win'
    BLACK_WIN = 'black_win'
    DRAW = 'draw'

class Move:
    """
    Represents a move in the chess game.
    """
    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.piece = start.piece

class Game:
    """
    Represents the chess game, managing the board and players.
    """
    def __init__(self):
        self.board = Board.get_instance()
        self.players = [Player(True, "Player 1"), Player(False, "Player 2")]
        self.is_white_turn = True
        self.current_state = GameState.IN_PROGRESS

    def is_valid_move(self, move):
        # Basic validation: check if piece exists and belongs to current player
        if move.start.piece is None:
            return False
        if move.start.piece.is_white != self.is_white_turn:
            return False
        return move.start.piece.can_move(self.board, move.start, move.end)

    def make_move(self, start_row, start_col, end_row, end_col):
        start_cell = self.board.board[start_row][start_col]
        end_cell = self.board.board[end_row][end_col]
        move = Move(start_cell, end_cell)

        if self.is_valid_move(move):
            if end_cell.piece is not None:
                end_cell.piece.is_killed = True
                if isinstance(end_cell.piece, King):
                    self.current_state = GameState.WHITE_WIN if self.is_white_turn else GameState.BLACK_WIN
            end_cell.piece = start_cell.piece
            start_cell.piece = None
            self.is_white_turn = not self.is_white_turn
            return True
        return False

    def start(self, move_provider):
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
            if not self.make_move(start_row, start_col, end_row, end_col):
                print("Invalid move, try again.")
            else:
                print(f"Moved from ({start_row},{start_col}) to ({end_row},{end_col})")
            # Optionally, print the board here for debugging

def console_move_provider(game):
    try:
        move_str = input("Enter move as 'start_row start_col end_row end_col': ")
        return tuple(map(int, move_str.strip().split()))
    except Exception:
        print("Invalid input format.")
        return None

def play_chess_game():
    """
    Function to create a Game instance and start the chess game using console input.
    """
    game = Game()
    game.start(console_move_provider)
    if game.current_state == GameState.WHITE_WIN:
        print("White wins!")
    elif game.current_state == GameState.BLACK_WIN:
        print("Black wins!")
    elif game.current_state == GameState.DRAW:
        print("Game is a draw.")
    else:
        print("Game ended.")

# To play the game, call:
# play_chess_game()