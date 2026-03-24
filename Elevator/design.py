from enum import Enum
from abc import ABC, abstractmethod

class Direction(Enum):
    IDLE = 'IDLE'
    UP = 'UP'
    DOWN = 'DOWN'

class State(Enum):
    IDLE = 'IDLE'
    MOVING = 'MOVING'
    MAINTENANCE = 'MAINTENANCE'
    STOPPED = 'STOPPED'

class Floor:
    def __init__(self, floor_number: int):
        self.floor_number = floor_number

class SchedulingStrategy(ABC):
    def __init__(self):
        pass
    
    @abstractmethod
    def get_next_floor(self, elevator: Elevator):
        pass

class FCFSStrategy(SchedulingStrategy):
    def get_next_floor(self, elevator: Elevator):
        pass

class ElevatorController:
    def __init__(self, elevators: list[Elevator], floors: list[Floor], strategy: SchedulingStrategy):
        self.elevators = elevators
        self.floors = floors
        self.scheduling_strategy = strategy


class ElevatorObserver(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def onFloorChange(self, floor, elevator):
        pass

    @abstractmethod
    def onStateChange(self, state, elevator):
        pass

class DisplayObserver(ElevatorObserver):
    def onFloorChange(self, floor, elevator):
        print(f"Floor changed to {floor} for elevator with id: {elevator.id}")
    
    def onStateChange(self, state, elevator):
        print(f"State changed to {state} for elevator with id: {elevator.id}")

class ElevatorRequest:
    def __init__(self):
        pass

class Elevator:
    def __init__(self, id, observers: list[ElevatorObserver], requests: list[ElevatorRequest] ):
        self.id = id
        self.current_floor = 0
        self.direction = Direction.IDLE
        self.observers = observers
        self.requests = requests
        self.state = State.IDLE


class Building:
    def __init__(self, name: str, elevator_controller: ElevatorController, number_of_floors: int):
        self.name = name
        self.elevator_controller = elevator_controller
        self.number_of_floors = number_of_floors
