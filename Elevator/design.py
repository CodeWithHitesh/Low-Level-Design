from enum import Enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Deque
from collections import deque


class Direction(Enum):
    IDLE = 'IDLE'
    UP = 'UP'
    DOWN = 'DOWN'


class State(Enum):
    IDLE = 'IDLE'
    MOVING = 'MOVING'
    MAINTENANCE = 'MAINTENANCE'


@dataclass
class Floor:
    floorNum: int 


# STRATEGY PATTERN 
class SchedulingStrategy(ABC):
    @abstractmethod
    def get_next_floor(self, elevator: Elevator) -> Floor:
        pass


class FCFSStrategy(SchedulingStrategy):
    def get_next_floor(self, elevator: Elevator):
        requests = elevator.requests
        if requests:
            return requests[0].floor
        return elevator.floor


class ScanStrategy(SchedulingStrategy):
    # Iterate in one direction till all requests are over
    def getClosestUpAndDownFloors(self, requests, currentFloor: Floor):
        currentFloorNum = currentFloor.floorNum
        closestUpFloor = Floor(currentFloorNum)
        closestDownFloor = Floor(currentFloorNum)

        for request in requests:
            floor_num = request.floor.floorNum
            
            if floor_num > currentFloorNum:
                if closestUpFloor.floorNum == currentFloorNum or floor_num < closestUpFloor.floorNum:
                    closestUpFloor = Floor(floor_num)
            elif floor_num < currentFloorNum:
                if closestDownFloor.floorNum == currentFloorNum or floor_num > closestDownFloor.floorNum:
                    closestDownFloor = Floor(floor_num)
        
        return (closestDownFloor, closestUpFloor)

    def get_next_floor(self, elevator: Elevator) -> Floor:
        
        currentFloor = elevator.floor
        currentFloorNum = currentFloor.floorNum
        currentDirection = elevator.direction
        currentState = elevator.state
        requests = elevator.requests

        if not len(requests):
            return currentFloor
        
        closestDownFloor, closestUpFloor = self.getClosestUpAndDownFloors(requests, currentFloor)

        if currentState == State.IDLE:
            if closestUpFloor.floorNum == currentFloorNum:
                nextFloor = closestDownFloor
            elif closestDownFloor.floorNum == currentFloorNum:
                nextFloor = closestUpFloor
            else:
                up_dist = closestUpFloor.floorNum - currentFloorNum
                down_dist = currentFloorNum - closestDownFloor.floorNum
                nextFloor = closestUpFloor if up_dist < down_dist else closestDownFloor
        elif currentDirection == Direction.UP:
            nextFloor = closestUpFloor if closestUpFloor.floorNum != currentFloorNum else closestDownFloor
        else:  # DOWN
            nextFloor = closestDownFloor if closestDownFloor.floorNum != currentFloorNum else closestUpFloor

        return nextFloor


class LookStrategy(SchedulingStrategy):
    def get_next_floor(self, elevator: Elevator) -> Floor:
        requests = elevator.requests

        currentFloor = elevator.floor
        currentFloorNum = currentFloor.floorNum

        if not len(requests):
            return currentFloor

        targetFloor = requests[0].floor
        targetFloorNum = targetFloor.floorNum

        if targetFloorNum == currentFloorNum:
            return currentFloor
        
        candidate = targetFloor
        direction = Direction.UP if targetFloorNum > currentFloorNum else Direction.DOWN

        for request in requests:
            reqFloor = request.floor
            if direction == Direction.UP and currentFloorNum < reqFloor.floorNum < targetFloorNum:
                if request.isInternalRequest() or (isinstance(request, ExternalElevatorRequest) and request.direction == direction):
                    if reqFloor.floorNum < candidate.floorNum:
                        candidate = reqFloor
            elif direction == Direction.DOWN and targetFloorNum < reqFloor.floorNum < currentFloorNum:
                if request.isInternalRequest() or (isinstance(request, ExternalElevatorRequest) and request.direction == direction):
                    if reqFloor.floorNum > candidate.floorNum:
                        candidate = reqFloor

        return candidate


# COMMAND PATTERN
class ElevatorCommand(ABC):
    @abstractmethod
    def execute(self):
        pass


@dataclass
class ElevatorRequest(ElevatorCommand):
    controller: ElevatorController
    floor: Floor
    elevatorId: int

    @abstractmethod
    def isInternalRequest(self) -> bool:
        pass


@dataclass
class InternalElevatorRequest(ElevatorRequest):

    def execute(self):
        return self.controller.requestFloor(self.elevatorId, self.floor)
    
    def isInternalRequest(self):
        return True 


@dataclass
class ExternalElevatorRequest(ElevatorRequest):
    direction: Direction

    def execute(self):
        return self.controller.requestElevator(self.elevatorId, self.direction, self.floor)

    def isInternalRequest(self) -> bool:
        return False 


@dataclass
class Elevator:
    id: int 
    floor: Floor  = field(default_factory=lambda: Floor(0))
    direction: Direction = field(default=Direction.IDLE)
    state: State = field(default=State.IDLE)
    requests: Deque[ElevatorRequest] = field(default_factory=deque)
    observers: List[ElevatorObserver] = field(default_factory=list)

    def moveToNextFloor(self, nextFloor: Floor):
        self.direction = Direction.UP if nextFloor.floorNum > self.floor.floorNum else Direction.DOWN
        self.floor = nextFloor
        self.state = State.MOVING
        self.requests = deque(req for req in self.requests if req.floor != nextFloor)
        self.notifyObserversOnFloorChange(self.floor)

    def notifyObserversOnFloorChange(self, floor):
        for observer in self.observers:
            observer.onFloorChange(floor, self)
    
    def notifyObserversOnStateChange(self, state):
        for observer in self.observers:
            observer.onStateChange(state, self)


@dataclass
class ElevatorController:
    floors: List[Floor]
    strategy: SchedulingStrategy
    elevators: List[Elevator] = field(default_factory=list)

    def requestFloor(self, elevatorId: int,  floor: Floor):
        elevator = self.getElevatorById(elevatorId)
        if elevator:
            elevator.requests.append(InternalElevatorRequest(self, floor, elevatorId))

    def requestElevator(self, elevatorId: int, direction: Direction, floor: Floor):
        elevator = self.getElevatorById(elevatorId)
        if elevator:
            elevator.requests.append(ExternalElevatorRequest(self, floor, elevatorId, direction))

    def getElevatorById(self, elevatorId: int):

        for elevator in self.elevators:
            if elevator.id == elevatorId:
                return elevator
        
        return None 

    # Perform a simulation step by moving all elevators
    def step(self):

        for elevator in self.elevators:
            if len(elevator.requests) > 0:
                nextFloor = self.strategy.get_next_floor(elevator)
                elevator.moveToNextFloor(nextFloor)


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


@dataclass
class Building:
    id: int 
    name: str 
    numOfFloor: int 


@dataclass
class BuildingController:
    building: Building
    elevatorController: ElevatorController