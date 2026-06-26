"""Parking Lot implementation."""

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
    def calculateFee(self, vehicle_type: VehicleType, duration: int,
                     duration_type: DurationType) -> float:
        pass


class BasicHourlyFeeStrategy(ParkingFeeStrategy):
    def calculateFee(self, vehicle_type: VehicleType, duration: int,
                     duration_type: DurationType) -> float:
        rates = {VehicleType.CAR: 10, VehicleType.BIKE: 5}
        hourly = rates.get(vehicle_type, 10)
        total = hourly * duration
        if duration_type == DurationType.DAYS:
            total *= 24
        return total


class PremiumHourlyFeeStrategy(ParkingFeeStrategy):
    """Higher rates for premium zones / peak hours."""
    pass


# ─── Vehicle & Factory ────────────────────────────────────────

@dataclass
class Vehicle(ABC):
    """Abstract vehicle that delegates fee calculation to a strategy."""
    license_plate: str
    vehicle_type: VehicleType
    fee_strategy: ParkingFeeStrategy

    @abstractmethod
    def calculateFee(self, duration: int, duration_type: DurationType) -> float:
        pass


class Car(Vehicle):
    def calculateFee(self, duration: int, duration_type: DurationType) -> float:
        return self.fee_strategy.calculateFee(self.vehicle_type, duration, duration_type)


class Bike(Vehicle):
    def calculateFee(self, duration: int, duration_type: DurationType) -> float:
        return self.fee_strategy.calculateFee(self.vehicle_type, duration, duration_type)


class VehicleFactory:
    """Centralises vehicle creation. Easy to extend for new types."""

    @staticmethod
    def create(license_plate: str, vehicle_type: VehicleType,
               fee_strategy: ParkingFeeStrategy) -> Vehicle:
        vehicle_type_map = {
            VehicleType.CAR: Car,
            VehicleType.BIKE: Bike,
        }
        cls = vehicle_type_map.get(vehicle_type)
        if not cls:
            raise ValueError(f"Unknown vehicle type: {vehicle_type}")
        return cls(license_plate, vehicle_type, fee_strategy)


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
    def __init__(self, amount: float, payment_strategy: PaymentStrategy):
        self.amount = amount
        self.payment_strategy = payment_strategy

    def processPayment(self) -> bool:
        if self.amount <= 0:
            raise ValueError("Invalid payment amount")
        return self.payment_strategy.processPayment(self.amount)


# ─── Parking Slot ─────────────────────────────────────────────

@dataclass
class ParkingSlot:
    """A single slot on a floor, typed for a specific vehicle."""
    spot_number: int
    slot_type: VehicleType
    vehicle: Optional[Vehicle] = field(default=None)
    is_occupied: bool = field(default=False)

    def parkVehicle(self, vehicle: Vehicle) -> None:
        if self.is_occupied:
            raise ValueError(f"Slot {self.spot_number} already occupied")
        self.vehicle = vehicle
        self.is_occupied = True

    def vacateSlot(self) -> None:
        self.vehicle = None
        self.is_occupied = False


# ─── Parking Floor ────────────────────────────────────────────

@dataclass
class ParkingFloor:
    """A floor containing multiple parking slots."""
    floor_number: int
    parking_slots: List[ParkingSlot]

    def findAvailableSlot(self, vehicle_type: VehicleType) -> Optional[ParkingSlot]:
        for slot in self.parking_slots:
            if not slot.is_occupied and slot.slot_type == vehicle_type:
                return slot
        return None


# ─── Parking Lot (Composition) ───────────────────────────────

@dataclass
class ParkingLot:
    """
    Top-level orchestrator.
    Composition: ParkingLot → ParkingFloor → ParkingSlot
    """
    parking_floors: List[ParkingFloor]

    def findAvailableSlot(self, vehicle_type: VehicleType) -> Optional[ParkingSlot]:
        for floor in self.parking_floors:
            slot = floor.findAvailableSlot(vehicle_type)
            if slot:
                return slot
        return None

    def parkVehicle(self, vehicle: Vehicle) -> None:
        """Find an available slot and park the vehicle."""
        slot = self.findAvailableSlot(vehicle.vehicle_type)
        if not slot:
            raise ValueError(f"No available slot for {vehicle.vehicle_type.value}")
        slot.parkVehicle(vehicle)
        print(f"{vehicle.license_plate} parked at slot {slot.spot_number}.")

    def vacateSlot(self, slot: ParkingSlot, vehicle: Vehicle) -> None:
        """Free a slot and mark it as vacant."""
        if not slot.is_occupied:
            raise ValueError("Slot is already vacant")
        if slot.vehicle != vehicle:
            raise ValueError("This vehicle is not parked in this slot")
        slot.vacateSlot()
        print(f"Slot {slot.spot_number} vacated. {vehicle.license_plate} exited.")


# ─── Demo ───────────────────────────────────────────────────────

if __name__ == "__main__":
    fee_strategy = BasicHourlyFeeStrategy()
    car = VehicleFactory.create("KA-01-1234", VehicleType.CAR, fee_strategy)
    bike = VehicleFactory.create("KA-01-5678", VehicleType.BIKE, fee_strategy)

    slots_floor1 = [
        ParkingSlot(spot_number=1, slot_type=VehicleType.CAR),
        ParkingSlot(spot_number=2, slot_type=VehicleType.CAR),
        ParkingSlot(spot_number=3, slot_type=VehicleType.BIKE),
    ]
    floor1 = ParkingFloor(floor_number=1, parking_slots=slots_floor1)
    lot = ParkingLot(parking_floors=[floor1])

    lot.parkVehicle(car)
    lot.parkVehicle(bike)

    fee = car.calculateFee(3, DurationType.HOURS)
    print(f"Fee for {car.license_plate}: ₹{fee}")

    lot.vacateSlot(slots_floor1[0], car)