from abc import ABC, abstractmethod
from enum import Enum
from collections import deque
from math import ceil
from random import randint


class CellValues(Enum):
    EMPTY = 'EMPTY'
    FRUIT = 'FRUIT'
    SNAKE = 'SNAKE'


# TEMPLATE DESIGN PATTERN
class MoveSnake(ABC):
    def move(self, snake, pos_x, pos_y, board):
        snake.appendleft([pos_x, pos_y])
        board[pos_x][pos_y] = CellValues.SNAKE
        return self._move(snake, board)
    
    @abstractmethod
    def _move(self, snake, board):
        pass


class MoveSnakeFruit(MoveSnake):
    def _move(self, snake, board):
        return snake, board


class MoveSnakeEmpty(MoveSnake):
    def _move(self, snake, board):
        last_x, last_y = snake.pop()
        board[last_x][last_y] = CellValues.EMPTY
        return snake, board


class Board:
    def __init__(self, n_row, n_col, snake_len=1, n_fruits=0 ):
        self.grid = [ [ CellValues.EMPTY for _ in range(n_col) ] for _ in range(n_row) ]
        self.init_snake(snake_len, n_row, n_col)
        self.init_fruits(n_fruits, n_row, n_col)
    
    def init_fruits(self, n_fruits, n_row, n_col):
        if not n_fruits:
            n_fruits = ceil( (n_col*n_row) / 5)
        
        while n_fruits:
            rand_i, rand_j = randint(0, n_row-1), randint(0, n_col-1)

            if self.grid[rand_i][rand_j] == CellValues.EMPTY:
                self.grid[rand_i][rand_j] = CellValues.FRUIT
                n_fruits -= 1
    
    def spawn_new_fruit(self):
        n_row, n_col = len(self.grid), len(self.grid[0])
        
        has_empty = False
        for i in range(n_row):
            for j in range(n_col):
                if self.grid[i][j] == CellValues.EMPTY:
                    has_empty = True
                    break
            if has_empty:
                break
        
        if not has_empty:
            return
        
        n_fruits = 1
        while n_fruits:
            rand_i, rand_j = randint(0, n_row-1), randint(0, n_col-1)
            if self.grid[rand_i][rand_j] == CellValues.EMPTY:
                self.grid[rand_i][rand_j] = CellValues.FRUIT
                n_fruits -= 1

    def init_snake(self, snake_len, n_row, n_col):
        self.snake = deque()
        
        self.snake.append([n_row//2, n_col//2])
        self.grid[n_row//2][n_col//2] = CellValues.SNAKE

        for _ in range(snake_len - 1):
            last_pos = self.snake[-1]
            new_pos = [last_pos[0], ( last_pos[1] + 1 ) % len(self.grid[0])]
            self.snake.append(new_pos)
            self.grid[new_pos[0]][new_pos[1]] = CellValues.SNAKE
    
    def get_snake(self):
        return self.snake
    
    def get_grid(self):
        return self.grid
    
    def move_snake(self, new_head_x, new_head_y, cellvalue):
        strategy = {
            CellValues.EMPTY : MoveSnakeEmpty(),
            CellValues.FRUIT : MoveSnakeFruit()
        }
        self.snake, self.grid = strategy.get(cellvalue).move(self.snake, new_head_x, new_head_y, self.grid)

        if cellvalue == CellValues.FRUIT:
            self.spawn_new_fruit()

        return self.snake, self.grid
    
    def display(self):

        print("\n\n\nThe current state of the game board: \n")

        for i in range(len(self.grid)):
            for j in range(len(self.grid[0])):
                print(f"{self.grid[i][j].value[0]} ")
            print("\n")


class Direction(Enum):
    UP = [-1, 0]
    DOWN = [1, 0]
    RIGHT = [0, 1]
    LEFT = [0, -1] 


# STRATEGY DESIGN PATTERN
class PlayerStrategy(ABC):
    @abstractmethod
    def make_move(self, board):
        pass 


class HumanPlayerStrategy(PlayerStrategy):
    def make_move(self, board):
        while True:
            choice = (str(input('Enter direction to move out of: UP, DOWN, RIGHT and LEFT'))).upper()
            try:
                coordinates = Direction[choice].value
                return coordinates
            except KeyError:
                print("Please enter valid direction!")


class Player:
    def __init__(self, name, strategy):
        self.name = name
        self.strategy = strategy
    
    def make_move(self, board):
        return self.strategy.make_move(board)


# FACTORY DESIGN PATTERN
class PlayerFactory:
    @staticmethod
    def create(name, player_type):
        strategies = {
            'human': HumanPlayerStrategy()
        }
        strategy = strategies.get(player_type.lower(), HumanPlayerStrategy())
        return Player(name, strategy)


class GameState(Enum):
    IN_PROGRESS = 'IN_PROGRESS'
    GAME_OVER = 'GAME_OVER'


class Game:
    def __init__(self, player_name, player_type, n_row, n_col, snake_len, n_fruits):
        self.player = PlayerFactory.create(player_name, player_type)
        self.board = Board(n_row, n_col, snake_len, n_fruits)
        self.curr_state = GameState.IN_PROGRESS
    
        self.snake = self.board.get_snake()
        self.grid = self.board.get_grid()

    def play(self):
        while self.curr_state == GameState.IN_PROGRESS:
            dir_x, dir_y = self.player.make_move(self.board)
            
            head_x, head_y = self.snake[0]
            
            new_head_x, new_head_y = dir_x + head_x, (dir_y + head_y) % len(self.grid[0])

            if not (0 <= new_head_x < len(self.grid)):
                self.curr_state = GameState.GAME_OVER
                print("Game Over! Hit Vertical Boundary!\n")

            elif self.grid[new_head_x][new_head_y] == CellValues.SNAKE and [new_head_x, new_head_y] != self.snake[-1]:
                self.curr_state = GameState.GAME_OVER
                print("Game Over! Hit Itself!\n")
            
            elif self.grid[new_head_x][new_head_y] == CellValues.FRUIT:
                self.snake, self.grid = self.board.move_snake(new_head_x, new_head_y, CellValues.FRUIT)
            
            else:
                self.snake, self.grid = self.board.move_snake(new_head_x, new_head_y, CellValues.EMPTY)

            self.board.display()