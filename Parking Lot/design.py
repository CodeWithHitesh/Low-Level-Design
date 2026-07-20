from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from math import ceil
import threading
from typing import Dict, List, Optional


# ─── Enums ────────────────────────────────────────────────────

class VehicleType(Enum):
    CAR = "car"
    BIKE = "bike"


# ─── Fee Strategy (Strategy Pattern) ─────────────────────────

class ParkingFeeStrategy(ABC):
    @abstractmethod
    def calculateFee(self, vehicle: "Vehicle", duration_hours: int) -> float:
        pass


class BasicHourlyFeeStrategy(ParkingFeeStrategy):
    def calculateFee(self, vehicle: "Vehicle", duration_hours: int) -> float:
        if duration_hours <= 0:
            raise ValueError("Duration must be positive")

        return vehicle.base_rate * duration_hours


class PremiumHourlyFeeStrategy(ParkingFeeStrategy):
    """Higher rates for premium zones / peak hours."""

    def __init__(self, multiplier: float = 1.5) -> None:
        if multiplier <= 1:
            raise ValueError("Premium multiplier must be greater than 1")
        self.multiplier = multiplier

    def calculateFee(self, vehicle: "Vehicle", duration_hours: int) -> float:
        if duration_hours <= 0:
            raise ValueError("Duration must be positive")

        premium_hourly = vehicle.base_rate * self.multiplier
        return premium_hourly * duration_hours


# ─── Vehicle & Factory ────────────────────────────────────────

@dataclass
class Vehicle(ABC):
    """Abstract vehicle that delegates fee calculation to a strategy."""
    license_plate: str
    vehicle_type: VehicleType
    fee_strategy: ParkingFeeStrategy
    base_rate: float

    @abstractmethod
    def calculateFee(self, duration_hours: int) -> float:
        pass


class Car(Vehicle):
    def __init__(self, license_plate: str, fee_strategy: ParkingFeeStrategy) -> None:
        super().__init__(license_plate, VehicleType.CAR, fee_strategy, 10)

    def calculateFee(self, duration_hours: int) -> float:
        return self.fee_strategy.calculateFee(self, duration_hours)


class Bike(Vehicle):
    def __init__(self, license_plate: str, fee_strategy: ParkingFeeStrategy) -> None:
        super().__init__(license_plate, VehicleType.BIKE, fee_strategy, 5)

    def calculateFee(self, duration_hours: int) -> float:
        return self.fee_strategy.calculateFee(self, duration_hours)


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
        return cls(license_plate, fee_strategy)


# ─── Payment (Strategy Pattern) ──────────────────────────────

class PaymentStrategy(ABC):
    @abstractmethod
    def processPayment(self, amount: float) -> bool:
        pass


class CreditCardPayment(PaymentStrategy):
    """Credit card payment strategy."""

    def processPayment(self, amount: float) -> bool:
        print(f"Credit Card Payment: ₹{amount}")
        return True


class CashPayment(PaymentStrategy):
    """Cash payment strategy."""

    def processPayment(self, amount: float) -> bool:
        print(f"Cash Payment: ₹{amount}")
        return True


@dataclass
class Payment:
    """Wraps an amount and delegates to a payment strategy."""
    amount: float
    payment_strategy: PaymentStrategy

    def processPayment(self) -> bool:
        if self.amount <= 0:
            raise ValueError("Invalid payment amount")
        return self.payment_strategy.processPayment(self.amount)


class PaymentProcessor:
    """Coordinates payment execution independent of parking lifecycle."""

    def process(self, amount: float, payment_strategy: PaymentStrategy) -> None:
        payment = Payment(amount=amount, payment_strategy=payment_strategy)
        if not payment.processPayment():
            raise ValueError("Payment failed")


# ─── Parking Slot ─────────────────────────────────────────────

@dataclass
class Ticket:
    ticket_id: int
    vehicle: Vehicle
    slot: 'ParkingSlot'
    entry_time: datetime
    exit_time: Optional[datetime] = None
    amount: Optional[float] = None


@dataclass
class ParkingSlot:
    """A single slot on a floor, typed for a specific vehicle."""
    spot_number: int
    slot_type: VehicleType
    vehicle: Optional[Vehicle] = field(default=None)

    def parkVehicle(self, vehicle: Vehicle) -> None:
        if self.isOccupied():
            raise ValueError(f"Slot {self.spot_number} already occupied")
        
        if self.slot_type != vehicle.vehicle_type:
            raise ValueError(f"Slot type: {self.slot_type} different from vehicle type {vehicle.vehicle_type}")

        self.vehicle = vehicle

    def vacateSlot(self) -> None:
        self.vehicle = None

    def isOccupied(self) -> bool:
        return self.vehicle is not None

# ─── Parking Floor ────────────────────────────────────────────

@dataclass
class ParkingFloor:
    """A floor containing multiple parking slots."""
    floor_number: int
    parking_slots: List[ParkingSlot]

    def findAvailableSlot(self, vehicle_type: VehicleType) -> Optional[ParkingSlot]:
        for slot in self.parking_slots:
            if not slot.isOccupied() and slot.slot_type == vehicle_type:
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
    active_tickets: Dict[int, Ticket] = field(default_factory=dict)
    next_ticket_id: int = 1
    payment_processor: PaymentProcessor = field(default_factory=PaymentProcessor)
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def findAvailableSlot(self, vehicle_type: VehicleType) -> Optional[ParkingSlot]:
        for floor in self.parking_floors:
            slot = floor.findAvailableSlot(vehicle_type)
            if slot:
                return slot
        return None

    def parkVehicle(self, vehicle: Vehicle) -> Ticket:
        """Find an available slot, park the vehicle, and issue a ticket."""
        with self.lock:
            slot = self.findAvailableSlot(vehicle.vehicle_type)
            if not slot:
                raise ValueError(f"No available slot for {vehicle.vehicle_type.value}")

            slot.parkVehicle(vehicle)
            ticket = Ticket(
                ticket_id=self.next_ticket_id,
                vehicle=vehicle,
                slot=slot,
                entry_time=datetime.now(),
            )
            self.active_tickets[ticket.ticket_id] = ticket
            self.next_ticket_id += 1
        
        print(f"{vehicle.license_plate} parked at slot {slot.spot_number}.")
        return ticket

    def _getActiveTicket(self, ticket: Ticket) -> Ticket:
        active_ticket = self.active_tickets.get(ticket.ticket_id)
        if active_ticket is None:
            raise ValueError("Invalid or inactive ticket")
        return active_ticket

    def _calculateDurationHours(self, entry_time: datetime, exit_time: Optional[datetime] = None) -> int:
        end_time = exit_time or datetime.now()
        if end_time < entry_time:
            raise ValueError("Exit time cannot be before entry time")
        parked_seconds = (end_time - entry_time).total_seconds()
        return max(1, ceil(parked_seconds / 3600))

    def _calculateParkingFee(self, ticket: Ticket) -> float:
        """Compute fee for an active ticket. Must be called inside a lock context."""
        active_ticket = self._getActiveTicket(ticket)
        duration_hours = self._calculateDurationHours(active_ticket.entry_time)
        return active_ticket.vehicle.calculateFee(duration_hours)

    def exitVehicle(self, ticket: Ticket, payment_strategy: PaymentStrategy) -> None:
        """Process payment for a ticket and free the associated slot."""
        with self.lock:
            active_ticket = self._getActiveTicket(ticket)
            amount = self._calculateParkingFee(ticket)

        # Payment is I/O-bound; run outside the lock so other threads are not blocked.
        self.payment_processor.process(amount, payment_strategy)

        with self.lock:
            active_ticket.amount = amount
            active_ticket.exit_time = datetime.now()
            active_ticket.slot.vacateSlot()
            del self.active_tickets[active_ticket.ticket_id]

        print(f"Slot {active_ticket.slot.spot_number} vacated. {active_ticket.vehicle.license_plate} exited.")


# ─── Demo ───────────────────────────────────────────────────────

if __name__ == "__main__":
    fee_strategy = BasicHourlyFeeStrategy()
    car = VehicleFactory.create("KA-01-1234", VehicleType.CAR, fee_strategy)
    bike = VehicleFactory.create("KA-01-5678", VehicleType.BIKE, fee_strategy)
    payment_strategy = CreditCardPayment()

    slots_floor1 = [
        ParkingSlot(spot_number=1, slot_type=VehicleType.CAR),
        ParkingSlot(spot_number=2, slot_type=VehicleType.CAR),
        ParkingSlot(spot_number=3, slot_type=VehicleType.BIKE),
    ]
    floor1 = ParkingFloor(floor_number=1, parking_slots=slots_floor1)
    lot = ParkingLot(parking_floors=[floor1])

    car_ticket = lot.parkVehicle(car)
    bike_ticket = lot.parkVehicle(bike)

    lot.exitVehicle(car_ticket, payment_strategy)