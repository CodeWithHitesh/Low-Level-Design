from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import List
from abc import ABC, abstractmethod


class VehicleType(Enum):
    Economy = 'Economy'
    Luxury = 'Luxury'
    Bike = 'Bike'


class VehicleStatus(Enum):
    Available = 'Available'
    Maintenance = 'Maintenance'


class ReservationStatus(Enum):
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"


# Observer Pattern
class Observer(ABC):
    @abstractmethod
    def notify(self, message):
        pass  


@dataclass
class User:
    id: int
    name: str 


@dataclass
class UserObserver(Observer):
    user: User
    
    def notify(self, message: str):
        print(f"{self.user.name} notified: {message}!")


@dataclass
class Vehicle(ABC):
    registrationNumber: str 
    model: str
    type: VehicleType
    baseRentalPrice: float 
    reservations: List['Reservation'] = field(default_factory=list)
    maintenanceStatus: VehicleStatus = field(default=VehicleStatus.Available)

    @abstractmethod
    def calculateRent(self, days):
        pass 

    def isAvailable(self, startDate, endDate):
        
        if self.maintenanceStatus == VehicleStatus.Maintenance:
            return False

        for reservation in self.reservations:
            if reservation.status == ReservationStatus.confirmed and reservation.overlaps(startDate, endDate):
                return False 
            
        return True 


class EconomyVehicle(Vehicle):
    rentalMultiplier = 1.0

    def calculateRent(self, days):
        return self.baseRentalPrice * self.rentalMultiplier * days
    

class LuxuryVehicle(Vehicle):
    rentalMultiplier = 2.0

    def calculateRent(self, days):
        return self.baseRentalPrice * self.rentalMultiplier * days


class Bike(Vehicle):
    rentalMultiplier = 0.5

    def calculateRent(self, days):
        return self.baseRentalPrice * self.rentalMultiplier * days


@dataclass
class Reservation:
    id: int 
    vehicle: Vehicle
    startDate: date 
    endDate: date 
    status: ReservationStatus 
    user: User

    def overlaps(self, startDate, endDate):
        return not (self.endDate < startDate or self.startDate > endDate)


@dataclass
class Location: 
    city: str 
    state: str 
    pinCode: int 
    address: str


@dataclass
class RentalStore:
    id: int 
    name: str 
    vehicles: List[Vehicle]
    location: Location

    def getAvailableVehicles(self, startDate: date, endDate: date) -> List[Vehicle]:
        return [v for v in self.vehicles if v.isAvailable(startDate, endDate)]

    def addVehicle(self, vehicle: Vehicle):
        self.vehicles.append(vehicle)
        return 
    
    def removeVehicle(self, registrationNum: str):
        
        for vehicle in self.vehicles:
            if vehicle.registrationNumber == registrationNum:
                self.vehicles.remove(vehicle)
                print(f"Vehicle with {registrationNum} removed!")
                return True 
        
        print(f"Vehicle with {registrationNum} not found!")
        return False 
    
    def isVehicleAvailable(self, registrationNum: str, startDate: date, endDate: date):
        
        for vehicle in self.vehicles:
            if vehicle.registrationNumber == registrationNum:
                return vehicle.isAvailable(startDate, endDate)
            
        return False


class VehicleFactory:
    
    @staticmethod
    def create_vehicle(vehicleType, model, registrationNumber, baseRentalPrice):
        vehicleTypes = {
            VehicleType.Bike: Bike,
            VehicleType.Economy: EconomyVehicle,
            VehicleType.Luxury: LuxuryVehicle
        } 
        vehicleClass = vehicleTypes.get(vehicleType, None)

        if not vehicleClass:
            print(f"Invalid Vehicle type: {vehicleType}")
            return None 

        return vehicleClass(registrationNumber, model, vehicleType, baseRentalPrice)


@dataclass
class ReservationManager:
    next_id: int = field(default=1)

    def makeReservation(self, user: User, vehicle: Vehicle, startDate: date, endDate: date):
        if not vehicle.isAvailable(startDate, endDate):
            raise ValueError("Vehicle not available for requested dates")
        reservation = Reservation(self.next_id, vehicle, startDate, endDate, ReservationStatus.confirmed, user) 
        self.next_id += 1
        vehicle.reservations.append(reservation)
        return reservation


class PaymentStrategy(ABC):

    @abstractmethod
    def processPayment(self, amount):
        pass 


class CashPayment(PaymentStrategy):
    def processPayment(self, amount):
        print(f"Processing amount : {amount} by Cash!")


class CardPayment(PaymentStrategy):
    def processPayment(self, amount):
        print(f"Processing amount : {amount} by Card!")


# Strategy Pattern
class PaymentProcessor:
    def processPayment(self, paymentStrategy: PaymentStrategy, amount: float):
        paymentStrategy.processPayment(amount)


# Singleton Pattern
class RentalSystem:
    _instance = None

    def __init__(self, rentalStores: List[RentalStore], vehicleFactory: VehicleFactory,
                 reservationManager: ReservationManager, paymentProcessor: PaymentProcessor):
        if RentalSystem._instance is not None:
            raise Exception("RentalSystem is a singleton — use get_instance()")
        self.rentalStores = rentalStores
        self.vehicleFactory = vehicleFactory
        self.reservationManager = reservationManager
        self.paymentProcessor = paymentProcessor
        self.observers: List[Observer] = []

    @classmethod
    def get_instance(cls, rentalStores: List[RentalStore], vehicleFactory: VehicleFactory,
                     reservationManager: ReservationManager, paymentProcessor: PaymentProcessor):
        if cls._instance is None:
            cls._instance = cls(rentalStores, vehicleFactory, reservationManager, paymentProcessor)
        return cls._instance

    def addObserver(self, observer: Observer):
        self.observers.append(observer)

    def notifyObservers(self, message: str):
        for observer in self.observers:
            observer.notify(message)

    def bookVehicle(self, user: User, store: RentalStore, registrationNum: str,
                    startDate: date, endDate: date, paymentStrategy: PaymentStrategy):
        for vehicle in store.vehicles:
            if vehicle.registrationNumber == registrationNum:
                reservation = self.reservationManager.makeReservation(user, vehicle, startDate, endDate)
                days = (endDate - startDate).days
                amount = vehicle.calculateRent(days)
                self.paymentProcessor.processPayment(paymentStrategy, amount)
                self.notifyObservers(f"Reservation {reservation.id} confirmed for {user.name}")
                return reservation
        raise ValueError(f"Vehicle {registrationNum} not found in store {store.name}")

    # TODO: searchVehicles(city, vehicleType, startDate, endDate) — search across stores
    # TODO: cancelReservation(reservationId) — cancel + refund logic
    # TODO: modifyReservation(reservationId, newDates) — reschedule
    # TODO: Add locking per vehicle in makeReservation for thread-safety under concurrent requests