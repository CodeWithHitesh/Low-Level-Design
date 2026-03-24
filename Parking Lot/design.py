"""
Parking Lot - Low Level Design

Design Patterns:
    - Strategy  → ParkingFeeStrategy, PaymentStrategy
    - Factory   → VehicleFactory
    - Composition → ParkingLot -> ParkingFloor -> ParkingSlot

Principles:
    - SRP: Each class has a single, well-defined responsibility
    - OCP: New fee strategies / payment methods without modifying existing code
    - DIP: High-level modules depend on abstractions (Strategy interfaces)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


# ─── Enums ────────────────────────────────────────────────────

class VehicleType(Enum):
    CAR = "car"
    BIKE = "bike"


class DurationType(Enum):
    HOURS = "hours"
    DAYS = "days"


# ─── Fee Strategy (Strategy Pattern) ─────────────────────────

class ParkingFeeStrategy(ABC):
    @abstractmethod
    def calculateFee(self, vehicleType: VehicleType, duration: int,
                     durationType: DurationType) -> float:
        pass


class BasicHourlyFeeStrategy(ParkingFeeStrategy):
    def calculateFee(self, vehicleType: VehicleType, duration: int,
                     durationType: DurationType) -> float:
        rates = {VehicleType.CAR: 10, VehicleType.BIKE: 5}
        hourly = rates.get(vehicleType, 10)
        total = hourly * duration
        if durationType == DurationType.DAYS:
            total *= 24
        return total


class PremiumHourlyFeeStrategy(ParkingFeeStrategy):
    """Higher rates for premium zones / peak hours."""
    pass


# ─── Vehicle & Factory ────────────────────────────────────────

@dataclass
class Vehicle(ABC):
    licensePlate: str
    vehicleType: VehicleType
    feeStrategy: ParkingFeeStrategy

    @abstractmethod
    def calculateFee(self, duration: int, durationType: DurationType) -> float:
        pass


class Car(Vehicle):
    def calculateFee(self, duration: int, durationType: DurationType) -> float:
        return self.feeStrategy.calculateFee(self.vehicleType, duration, durationType)


class Bike(Vehicle):
    def calculateFee(self, duration: int, durationType: DurationType) -> float:
        return self.feeStrategy.calculateFee(self.vehicleType, duration, durationType)


class VehicleFactory:
    """Centralises vehicle creation. Easy to extend for new types."""

    @staticmethod
    def createVehicle(licensePlate: str, vehicleType: VehicleType,
                      feeStrategy: ParkingFeeStrategy) -> Vehicle:
        vehicleTypeMap = {
            VehicleType.CAR: Car,
            VehicleType.BIKE: Bike,
        }
        cls = vehicleTypeMap.get(vehicleType, Car)
        return cls(licensePlate, vehicleType, feeStrategy)


# ─── Payment (Strategy Pattern) ──────────────────────────────

class PaymentStrategy(ABC):
    @abstractmethod
    def processPayment(self, amount: float) -> bool:
        pass


class CreditCardPayment(PaymentStrategy):
    def processPayment(self, amount: float) -> bool:
        print(f"Credit Card Payment: ₹{amount}")
        return True


class CashPayment(PaymentStrategy):
    def processPayment(self, amount: float) -> bool:
        print(f"Cash Payment: ₹{amount}")
        return True


class Payment:
    def __init__(self, amount: float, paymentStrategy: PaymentStrategy):
        self.amount = amount
        self.paymentStrategy = paymentStrategy

    def processPayment(self) -> bool:
        if self.amount <= 0:
            print("Invalid payment amount!")
            return False
        return self.paymentStrategy.processPayment(self.amount)


# ─── Parking Slot ─────────────────────────────────────────────

@dataclass
class ParkingSlot:
    spotNumber: int
    slotType: VehicleType
    vehicle: Optional[Vehicle] = field(default=None)
    isOccupied: bool = field(default=False)

    def parkVehicle(self, vehicle: Vehicle):
        if self.isOccupied:
            raise Exception(f"Slot {self.spotNumber} already occupied by {self.vehicle.licensePlate}")
        self.vehicle = vehicle
        self.isOccupied = True

    def vacateSlot(self):
        self.vehicle = None
        self.isOccupied = False


# ─── Parking Floor ────────────────────────────────────────────

@dataclass
class ParkingFloor:
    floorNumber: int
    parkingSlots: List[ParkingSlot]

    def findAvailableSlot(self, vehicleType: VehicleType) -> Optional[ParkingSlot]:
        for slot in self.parkingSlots:
            if not slot.isOccupied and slot.slotType == vehicleType:
                return slot
        return None


# ─── Parking Lot (Composition) ───────────────────────────────

@dataclass
class ParkingLot:
    """
    Top-level orchestrator.
    Composition: ParkingLot → ParkingFloor → ParkingSlot
    """
    parkingFloors: List[ParkingFloor]

    def findAvailableSlot(self, vehicleType: VehicleType) -> Optional[ParkingSlot]:
        for floor in self.parkingFloors:
            slot = floor.findAvailableSlot(vehicleType)
            if slot:
                return slot
        return None

    def parkVehicle(self, vehicle: Vehicle):
        slot = self.findAvailableSlot(vehicle.vehicleType)
        if not slot:
            print("No available slot found!")
            return

        slot.parkVehicle(vehicle)
        print(f"{vehicle.licensePlate} parked at slot {slot.spotNumber}.")

    def vacateSlot(self, slot: ParkingSlot, vehicle: Vehicle):
        if not slot.isOccupied:
            print("Slot is already vacant!")
            return

        if slot.vehicle != vehicle:
            print("This vehicle is not parked in this slot!")
            return

        slot.vacateSlot()
        print(f"Slot {slot.spotNumber} vacated. {vehicle.licensePlate} exited.")