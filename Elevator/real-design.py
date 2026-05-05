from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import List


# ──────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────

class Direction(Enum):
    IDLE = 'IDLE'
    UP = 'UP'
    DOWN = 'DOWN'


class State(Enum):
    IDLE = 'IDLE'
    MOVING = 'MOVING'
    MAINTENANCE = 'MAINTENANCE'


# ──────────────────────────────────────────────
# Requests
# ──────────────────────────────────────────────

@dataclass
class ElevatorRequest:
    floor: int

@dataclass
class InternalRequest(ElevatorRequest):
    pass

@dataclass
class ExternalRequest(ElevatorRequest):
    direction: Direction = None


# ──────────────────────────────────────────────
# Observer Pattern
# ──────────────────────────────────────────────

class ElevatorObserver(ABC):
    @abstractmethod
    def onFloorChange(self, floor, elevator):
        pass

    @abstractmethod
    def onStateChange(self, state, elevator):
        pass


class DisplayObserver(ElevatorObserver):
    def onFloorChange(self, floor, elevator):
        print(f"Elevator {elevator.id}: moved to floor {floor}")

    def onStateChange(self, state, elevator):
        print(f"Elevator {elevator.id}: state changed to {state.value}")


# ──────────────────────────────────────────────
# Elevator
# ──────────────────────────────────────────────

@dataclass
class Elevator:
    id: int
    currentFloor: int = 0
    direction: Direction = Direction.IDLE
    state: State = State.IDLE
    requests: List[ElevatorRequest] = field(default_factory=list)
    observers: List[ElevatorObserver] = field(default_factory=list)

    def addObserver(self, observer):
        self.observers.append(observer)

    def moveToFloor(self, floor: int):
        self.direction = Direction.UP if floor > self.currentFloor else Direction.DOWN
        self.state = State.MOVING
        self.currentFloor = floor
        self.notifyFloorChange()

        # Remove served requests
        self.requests = [r for r in self.requests if r.floor != floor]

        if not self.requests:
            self.state = State.IDLE
            self.direction = Direction.IDLE
            self.notifyStateChange()

    def notifyFloorChange(self):
        for observer in self.observers:
            observer.onFloorChange(self.currentFloor, self)

    def notifyStateChange(self):
        for observer in self.observers:
            observer.onStateChange(self.state, self)


# ──────────────────────────────────────────────
# Strategy Pattern — Elevator Selection
# ──────────────────────────────────────────────

class ElevatorSelectionStrategy(ABC):
    @abstractmethod
    def selectElevator(self, elevators: List[Elevator], request: ExternalRequest) -> Elevator:
        pass


class NearestElevatorStrategy(ElevatorSelectionStrategy):
    def selectElevator(self, elevators, request):
        return min(elevators, key=lambda e: abs(e.currentFloor - request.floor))


class FCFSStrategy(ElevatorSelectionStrategy):
    def selectElevator(self, elevators, request):
        for elevator in elevators:
            if elevator.state == State.IDLE:
                return elevator
        return elevators[0]


# ──────────────────────────────────────────────
# Controller
# ──────────────────────────────────────────────

class ElevatorController:
    def __init__(self, elevators: List[Elevator], strategy: ElevatorSelectionStrategy):
        self.elevators = elevators
        self.strategy = strategy

    def handleExternalRequest(self, floor: int, direction: Direction):
        request = ExternalRequest(floor, direction)
        elevator = self.strategy.selectElevator(self.elevators, request)
        elevator.requests.append(request)
        print(f"External request: floor {floor} {direction.value} → assigned to elevator {elevator.id}")

    def handleInternalRequest(self, elevatorId: int, floor: int):
        elevator = self.getElevatorById(elevatorId)
        if elevator:
            request = InternalRequest(floor)
            elevator.requests.append(request)
            print(f"Internal request: elevator {elevatorId} → go to floor {floor}")

    def getElevatorById(self, elevatorId: int):
        for elevator in self.elevators:
            if elevator.id == elevatorId:
                return elevator
        return None

    def step(self):
        """Process one move for each elevator — call repeatedly to simulate."""
        for elevator in self.elevators:
            if elevator.requests:
                nextFloor = elevator.requests[0].floor  # FCFS within elevator
                elevator.moveToFloor(nextFloor)


# ──────────────────────────────────────────────
# Building
# ──────────────────────────────────────────────

@dataclass
class Building:
    name: str
    numFloors: int
    controller: ElevatorController


# ──────────────────────────────────────────────
# Demo
# ──────────────────────────────────────────────

if __name__ == "__main__":
    # Setup
    e1 = Elevator(id=1, currentFloor=0)
    e2 = Elevator(id=2, currentFloor=5)

    display = DisplayObserver()
    e1.addObserver(display)
    e2.addObserver(display)

    strategy = NearestElevatorStrategy()
    controller = ElevatorController([e1, e2], strategy)
    building = Building("Office Tower", 10, controller)

    # User on floor 3 presses UP
    controller.handleExternalRequest(3, Direction.UP)

    # User on floor 7 presses DOWN
    controller.handleExternalRequest(7, Direction.DOWN)

    # Process — elevators move
    controller.step()

    # User inside elevator 1 presses floor 6
    controller.handleInternalRequest(1, 6)

    # Process again
    controller.step()
