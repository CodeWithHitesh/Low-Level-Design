from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import List
from datetime import date
import threading


# ─── Enums ────────────────────────────────────────────────────

class VehicleType(Enum):
    ECONOMY = "Economy"
    LUXURY = "Luxury"
    BIKE = "Bike"


class VehicleStatus(Enum):
    AVAILABLE = "Available"
    MAINTENANCE = "Maintenance"


class ReservationStatus(Enum):
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ─── Observer (Observer Pattern) ──────────────────────────────

class Observer(ABC):
    @abstractmethod
    def notify(self, message: str) -> None:
        pass


@dataclass
class User:
    id: int
    name: str


@dataclass
class UserObserver(Observer):
    """Notifies a specific user about rental events."""
    user: User

    def notify(self, message: str) -> None:
        print(f"{self.user.name} notified: {message}!")


# ─── Vehicle (ABC + Concrete Implementations) ────────────────

@dataclass
class Vehicle(ABC):
    """Abstract vehicle with rental pricing and availability logic."""
    registration_number: str
    model: str
    type: VehicleType
    base_rental_price: float
    reservations: List['Reservation'] = field(default_factory=list)
    status: VehicleStatus = field(default=VehicleStatus.AVAILABLE)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    @abstractmethod
    def calculateRent(self, days: int) -> float:
        pass

    def isAvailable(self, start_date: date, end_date: date) -> bool:
        """Check if vehicle is available for the given date range."""
        if self.status == VehicleStatus.MAINTENANCE:
            return False

        for reservation in self.reservations:
            if reservation.status == ReservationStatus.CONFIRMED and reservation.overlaps(start_date, end_date):
                return False

        return True


class EconomyVehicle(Vehicle):
    """Economy tier — base multiplier 1.0×."""
    rental_multiplier: float = 1.0

    def calculateRent(self, days: int) -> float:
        return self.base_rental_price * self.rental_multiplier * days


class LuxuryVehicle(Vehicle):
    """Luxury tier — premium multiplier 2.0×."""
    rental_multiplier: float = 2.0

    def calculateRent(self, days: int) -> float:
        return self.base_rental_price * self.rental_multiplier * days


class BikeVehicle(Vehicle):
    """Bike tier — discount multiplier 0.5×."""
    rental_multiplier: float = 0.5

    def calculateRent(self, days: int) -> float:
        return self.base_rental_price * self.rental_multiplier * days


# ─── Dataclass Models ─────────────────────────────────────────

@dataclass
class Reservation:
    """Represents a confirmed, completed, or cancelled booking."""
    id: int
    vehicle: Vehicle
    start_date: date
    end_date: date
    status: ReservationStatus
    user: User

    def overlaps(self, start_date: date, end_date: date) -> bool:
        return not (self.end_date < start_date or self.start_date > end_date)


@dataclass
class Location:
    city: str
    state: str
    pin_code: int
    address: str


@dataclass
class RentalStore:
    """A physical store that holds a fleet of vehicles."""
    id: int
    name: str
    vehicles: List[Vehicle]
    location: Location

    def getAvailableVehicles(self, start_date: date, end_date: date) -> List[Vehicle]:
        return [v for v in self.vehicles if v.isAvailable(start_date, end_date)]

    def addVehicle(self, vehicle: Vehicle) -> None:
        self.vehicles.append(vehicle)

    def removeVehicle(self, registration_num: str) -> bool:
        """Remove a vehicle by registration number. Raises RentalSystemError if not found."""
        for vehicle in list(self.vehicles):
            if vehicle.registration_number == registration_num:
                self.vehicles.remove(vehicle)
                return True

        raise ValueError(f"Vehicle with {registration_num} not found")

    def isVehicleAvailable(self, registration_num: str, start_date: date, end_date: date) -> bool:
        for vehicle in self.vehicles:
            if vehicle.registration_number == registration_num:
                return vehicle.isAvailable(start_date, end_date)
        return False


# ─── Factory ──────────────────────────────────────────────────

class VehicleFactory:
    """Centralises vehicle creation. Easy to extend for new types."""

    @staticmethod
    def create(vehicle_type: VehicleType, model: str,
               registration_number: str, base_rental_price: float) -> Vehicle:
        vehicle_types = {
            VehicleType.BIKE: BikeVehicle,
            VehicleType.ECONOMY: EconomyVehicle,
            VehicleType.LUXURY: LuxuryVehicle,
        }
        vehicle_class = vehicle_types.get(vehicle_type)
        if not vehicle_class:
            raise ValueError(f"Invalid vehicle type: {vehicle_type}")
        return vehicle_class(registration_number, model, vehicle_type, base_rental_price)


# ─── Reservation Manager ──────────────────────────────────────

@dataclass
class ReservationManager:
    """Thread-safe reservation creation and cancellation."""
    next_id: int = field(default=1)
    _id_lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def makeReservation(self, user: User, vehicle: Vehicle,
                        start_date: date, end_date: date) -> Reservation:
        with vehicle._lock:
            if not vehicle.isAvailable(start_date, end_date):
                raise ValueError("Vehicle not available for requested dates")
            with self._id_lock:
                reservation_id = self.next_id
                self.next_id += 1
            reservation = Reservation(
                reservation_id, vehicle, start_date, end_date,
                ReservationStatus.CONFIRMED, user
            )
            vehicle.reservations.append(reservation)
        return reservation

    def cancelReservation(self, reservation: Reservation) -> None:
        with reservation.vehicle._lock:
            if reservation.status != ReservationStatus.CONFIRMED:
                raise ValueError("Only confirmed reservations can be cancelled")
            reservation.status = ReservationStatus.CANCELLED


# ─── Payment (Strategy Pattern) ──────────────────────────────

class PaymentStrategy(ABC):
    @abstractmethod
    def processPayment(self, amount: float) -> None:
        pass


class CashPayment(PaymentStrategy):
    """Cash payment strategy."""

    def processPayment(self, amount: float) -> None:
        print(f"Processing amount: {amount} by Cash!")


class CardPayment(PaymentStrategy):
    """Card payment strategy."""

    def processPayment(self, amount: float) -> None:
        print(f"Processing amount: {amount} by Card!")


# ─── Orchestrator (Singleton) ─────────────────────────────────

class PaymentProcessor:
    """Delegates payment to the chosen strategy."""

    def processPayment(self, payment_strategy: PaymentStrategy, amount: float) -> None:
        payment_strategy.processPayment(amount)


class RentalSystem:
    """Singleton entry point for the car rental domain."""
    _instance = None
    _instance_lock = threading.Lock()

    def __init__(self, rental_stores: List[RentalStore], vehicle_factory: VehicleFactory,
                 reservation_manager: ReservationManager, payment_processor: PaymentProcessor):
        if RentalSystem._instance is not None:
            raise RuntimeError("RentalSystem is a singleton — use getInstance()")
        self.rental_stores = rental_stores
        self.vehicle_factory = vehicle_factory
        self.reservation_manager = reservation_manager
        self.payment_processor = payment_processor
        self.observers: List[Observer] = []

    @classmethod
    def getInstance(cls, rental_stores: List[RentalStore], vehicle_factory: VehicleFactory,
                     reservation_manager: ReservationManager,
                     payment_processor: PaymentProcessor) -> 'RentalSystem':
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls(rental_stores, vehicle_factory,
                                        reservation_manager, payment_processor)
        return cls._instance

    def addObserver(self, observer: Observer) -> None:
        self.observers.append(observer)

    def notifyObservers(self, message: str) -> None:
        for observer in self.observers:
            observer.notify(message)

    def bookVehicle(self, user: User, store_id: int, registration_num: str,
                    start_date: date, end_date: date,
                    payment_strategy: PaymentStrategy) -> Reservation:
        """Book a vehicle, process payment, and notify observers."""
        store = next((s for s in self.rental_stores if s.id == store_id), None)
        if not store:
            raise ValueError(f"Store with id {store_id} not found")
        for vehicle in store.vehicles:
            if vehicle.registration_number == registration_num:
                reservation = self.reservation_manager.makeReservation(
                    user, vehicle, start_date, end_date
                )
                days = (end_date - start_date).days + 1
                amount = vehicle.calculateRent(days)
                self.payment_processor.processPayment(payment_strategy, amount)
                self.notifyObservers(f"Reservation {reservation.id} confirmed for {user.name}")
                return reservation
        raise ValueError(f"Vehicle {registration_num} not found in store {store.name}")

    def cancelReservation(self, reservation: Reservation) -> None:
        self.reservation_manager.cancelReservation(reservation)
        self.notifyObservers(f"Reservation {reservation.id} has been cancelled")


# ─── Demo ─────────────────────────────────────────────────────

if __name__ == "__main__":
    factory = VehicleFactory()
    car = factory.create(VehicleType.ECONOMY, "Civic", "KA-01-1234", 500.0)
    bike = factory.create(VehicleType.BIKE, "Pulsar", "KA-01-5678", 200.0)

    location = Location("Bangalore", "Karnataka", 560001, "MG Road")
    store = RentalStore(1, "Downtown Hub", [car, bike], location)

    reservation_mgr = ReservationManager()
    payment_proc = PaymentProcessor()
    system = RentalSystem.getInstance([store], factory, reservation_mgr, payment_proc)

    user = User(1, "Alice")
    observer = UserObserver(user)
    system.addObserver(observer)

    reservation = system.bookVehicle(
        user, 1, "KA-01-1234", date(2026, 7, 1), date(2026, 7, 5), CashPayment()
    )
    print(f"Booked reservation #{reservation.id} for {car.model}")

    system.cancelReservation(reservation)
    print(f"Cancelled reservation #{reservation.id}")