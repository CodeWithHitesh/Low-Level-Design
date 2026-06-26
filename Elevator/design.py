"""Elevator System implementation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Deque, List


# ─── Enums ────────────────────────────────────────────────────

class Direction(Enum):
    IDLE = 'IDLE'
    UP = 'UP'
    DOWN = 'DOWN'


class State(Enum):
    IDLE = 'IDLE'
    MOVING = 'MOVING'
    MAINTENANCE = 'MAINTENANCE'


# ─── Dataclass Models ─────────────────────────────────────────

@dataclass
class Floor:
    floor_num: int


# ─── Observer (ABC) ───────────────────────────────────────────

class ElevatorObserver(ABC):
    @abstractmethod
    def onFloorChange(self, floor: Floor, elevator: Elevator) -> None:
        pass

    @abstractmethod
    def onStateChange(self, state: State, elevator: Elevator) -> None:
        pass


class DisplayObserver(ElevatorObserver):
    def onFloorChange(self, floor: Floor, elevator: Elevator) -> None:
        print(f"Floor changed to {floor.floor_num} for elevator {elevator.id}")

    def onStateChange(self, state: State, elevator: Elevator) -> None:
        print(f"State changed to {state.value} for elevator {elevator.id}")


# ─── Strategy Pattern (Scheduling) ───────────────────────────

class SchedulingStrategy(ABC):
    @abstractmethod
    def getNextFloor(self, elevator: Elevator) -> Floor:
        pass


class FCFSStrategy(SchedulingStrategy):
    """First-Come-First-Served: serve requests in arrival order."""

    def getNextFloor(self, elevator: Elevator) -> Floor:
        requests = elevator.requests
        if requests:
            return requests[0].floor
        return elevator.floor


class ScanStrategy(SchedulingStrategy):
    """Scan (elevator algorithm): serve closest in current direction, then reverse."""

    def getClosestUpAndDownFloors(self, requests: Deque[ElevatorRequest],
                                  current_floor: Floor) -> tuple:
        current_num = current_floor.floor_num
        closest_up = Floor(current_num)
        closest_down = Floor(current_num)

        for request in requests:
            floor_num = request.floor.floor_num

            if floor_num > current_num:
                if closest_up.floor_num == current_num or floor_num < closest_up.floor_num:
                    closest_up = Floor(floor_num)
            elif floor_num < current_num:
                if closest_down.floor_num == current_num or floor_num > closest_down.floor_num:
                    closest_down = Floor(floor_num)

        return (closest_down, closest_up)

    def getNextFloor(self, elevator: Elevator) -> Floor:
        current_floor = elevator.floor
        current_num = current_floor.floor_num
        current_direction = elevator.direction
        current_state = elevator.state
        requests = elevator.requests

        if not len(requests):
            return current_floor

        closest_down, closest_up = self.getClosestUpAndDownFloors(requests, current_floor)

        if current_state == State.IDLE:
            if closest_up.floor_num == current_num:
                next_floor = closest_down
            elif closest_down.floor_num == current_num:
                next_floor = closest_up
            else:
                up_dist = closest_up.floor_num - current_num
                down_dist = current_num - closest_down.floor_num
                next_floor = closest_up if up_dist < down_dist else closest_down
        elif current_direction == Direction.UP:
            next_floor = closest_up if closest_up.floor_num != current_num else closest_down
        else:
            next_floor = closest_down if closest_down.floor_num != current_num else closest_up

        return next_floor


class LookStrategy(SchedulingStrategy):
    """Look algorithm: like Scan but only goes as far as the last request."""

    def getNextFloor(self, elevator: Elevator) -> Floor:
        requests = elevator.requests
        current_floor = elevator.floor
        current_num = current_floor.floor_num

        if not len(requests):
            return current_floor

        target_floor = requests[0].floor
        target_num = target_floor.floor_num

        if target_num == current_num:
            return current_floor

        candidate = target_floor
        direction = Direction.UP if target_num > current_num else Direction.DOWN

        for request in requests:
            req_floor = request.floor
            if direction == Direction.UP and current_num < req_floor.floor_num < target_num:
                if request.isInternalRequest() or (isinstance(request, ExternalElevatorRequest) and request.direction == direction):
                    if req_floor.floor_num < candidate.floor_num:
                        candidate = req_floor
            elif direction == Direction.DOWN and target_num < req_floor.floor_num < current_num:
                if request.isInternalRequest() or (isinstance(request, ExternalElevatorRequest) and request.direction == direction):
                    if req_floor.floor_num > candidate.floor_num:
                        candidate = req_floor

        return candidate


# ─── Command Pattern (Requests) ───────────────────────────────

class ElevatorCommand(ABC):
    @abstractmethod
    def execute(self) -> None:
        pass


@dataclass
class ElevatorRequest(ElevatorCommand):
    """Base request command with a target floor."""
    controller: ElevatorController
    floor: Floor
    elevator_id: int

    @abstractmethod
    def isInternalRequest(self) -> bool:
        pass


@dataclass
class InternalElevatorRequest(ElevatorRequest):
    """Request from inside the elevator (passenger presses a floor button)."""

    def execute(self) -> None:
        self.controller.requestFloor(self.elevator_id, self.floor)

    def isInternalRequest(self) -> bool:
        return True


@dataclass
class ExternalElevatorRequest(ElevatorRequest):
    """Request from a floor (passenger calls the elevator)."""
    direction: Direction = field(default=Direction.UP)

    def execute(self) -> None:
        self.controller.requestElevator(self.elevator_id, self.direction, self.floor)

    def isInternalRequest(self) -> bool:
        return False


# ─── Elevator & Controller ────────────────────────────────────

@dataclass
class Elevator:
    """Represents a single elevator car with requests and observers."""
    id: int
    floor: Floor = field(default_factory=lambda: Floor(0))
    direction: Direction = field(default=Direction.IDLE)
    state: State = field(default=State.IDLE)
    requests: Deque[ElevatorRequest] = field(default_factory=deque)
    observers: List[ElevatorObserver] = field(default_factory=list)

    def moveToNextFloor(self, next_floor: Floor) -> None:
        self.direction = Direction.UP if next_floor.floor_num > self.floor.floor_num else Direction.DOWN
        self.floor = next_floor
        self.state = State.MOVING
        self.requests = deque(req for req in self.requests if req.floor != next_floor)
        self.notifyObserversOnFloorChange(self.floor)

    def notifyObserversOnFloorChange(self, floor: Floor) -> None:
        for observer in self.observers:
            observer.onFloorChange(floor, self)

    def notifyObserversOnStateChange(self, state: State) -> None:
        for observer in self.observers:
            observer.onStateChange(state, self)


@dataclass
class ElevatorController:
    """Orchestrates multiple elevators using a scheduling strategy."""
    floors: List[Floor]
    strategy: SchedulingStrategy
    elevators: List[Elevator] = field(default_factory=list)

    def requestFloor(self, elevator_id: int, floor: Floor) -> None:
        elevator = self.getElevatorById(elevator_id)
        if elevator:
            elevator.requests.append(InternalElevatorRequest(self, floor, elevator_id))

    def requestElevator(self, elevator_id: int, direction: Direction, floor: Floor) -> None:
        elevator = self.getElevatorById(elevator_id)
        if elevator:
            elevator.requests.append(ExternalElevatorRequest(self, floor, elevator_id, direction))

    def getElevatorById(self, elevator_id: int) -> Elevator:
        for elevator in self.elevators:
            if elevator.id == elevator_id:
                return elevator
        return None

    def step(self) -> None:
        """Perform one simulation step: move all elevators with pending requests."""
        for elevator in self.elevators:
            if len(elevator.requests) > 0:
                next_floor = self.strategy.getNextFloor(elevator)
                elevator.moveToNextFloor(next_floor)


# ─── Building Model ───────────────────────────────────────────

@dataclass
class Building:
    id: int
    name: str
    num_of_floors: int


@dataclass
class BuildingController:
    building: Building
    elevator_controller: ElevatorController


# ─── Demo ─────────────────────────────────────────────────────

if __name__ == "__main__":
    floors = [Floor(i) for i in range(10)]
    strategy = ScanStrategy()

    elevator1 = Elevator(id=1, observers=[DisplayObserver()])
    elevator2 = Elevator(id=2, observers=[DisplayObserver()])

    controller = ElevatorController(floors=floors, strategy=strategy, elevators=[elevator1, elevator2])

    controller.requestFloor(1, Floor(5))
    controller.requestFloor(1, Floor(3))
    controller.requestElevator(2, Direction.UP, Floor(7))

    for _ in range(3):
        controller.step()