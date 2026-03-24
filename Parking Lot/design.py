from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class VehicleType(Enum):
    car = 'car'
    bike = 'bike'


@dataclass
class Vehicle(ABC):
    licensePlate: str 
    vehicleType: VehicleType 
    feeStrategy: ParkingFeeStrategy

    @abstractmethod
    def calculateFee(self, duration, durationType):
        pass


class Car(Vehicle):
    def calculateFee(self, duration, durationType):
        self.feeStrategy.calculateFee(self.vehicleType, duration, durationType) 


class Bike(Vehicle):
    def calculateFee(self, duration, durationType):
        self.feeStrategy.calculateFee(self.vehicleType, duration, durationType)


# Factory Pattern not necessarily required in this problem 
class VehicleFactory():
    @staticmethod
    def createVehicle(licensePlate, vehicleType, feeStrategy):
        vehicleTypeMap = {
            VehicleType.car: Car,
            VehicleType.bike: Bike,
        }

        return vehicleTypeMap.get(vehicleType, Car)(licensePlate, vehicleType, feeStrategy)


class PaymentStrategy(ABC):
    @abstractmethod
    def processPayment(self, amount):
        pass


class CreditCardPayment(PaymentStrategy):
    def processPayment(self, amount):
        print(f"Card Payment Processing: {amount}!")


class CashPayment(PaymentStrategy):
    def processPayment(self, amount):
        print(f"Cash Payment Processing: {amount}!") 


class Payment:
    def __init__(self, amount: int, paymentStrategy: PaymentStrategy):
        self.paymentStrategy = paymentStrategy
        self.amount = amount

    def processPayment(self):
        if self.amount < 0:
            print("Invalid Payment Amount!")
            return
        self.paymentStrategy.processPayment(self.amount)


class DurationType(Enum):
    HOURS = 'hours'
    DAYS = 'days'


class ParkingFeeStrategy(ABC):
    @abstractmethod
    def calculateFee(self, vehicleType, duration, durationType):
        pass 


class BasicHourlyFeeStrategy(ParkingFeeStrategy):
    def calculateFee(self, vehicleType, duration, durationType):
        vehicleFee = {
            VehicleType.car: 10,
            VehicleType.bike: 5
        }

        hourlyFee = vehicleFee.get(vehicleType, 10)
        totalFee = hourlyFee * duration

        if durationType == DurationType.DAYS:
            totalFee *= 24  

        return totalFee

class PremiumHourlyFeeStrategy(ParkingFeeStrategy):
    pass


@dataclass
class ParkingSlot:
    spotNumber: int
    slotType: VehicleType
    vehicle: Optional[Vehicle] = field(default=None)
    isOccupied: Optional[bool] = field(default=False)

    def parkVehicle(self, vehicle):
        if self.isOccupied and self.vehicle is not None:
            raise Exception(f"Parking slot already occupied by vehicle: {self.vehicle.licensePlate}")
        
        self.vehicle = vehicle
        self.isOccupied = True
    
    def vacateSlot(self):
        self.isOccupied = False 
        self.vehicle = None


""" 
    Composite pattern can be used in the parking lot as well.
    For example, in a house we could have multiple floors, on
    each floor we could have multiple applicances. 
    Similarly, in parking lot:
    Parking Lot -> Multiple floors -> parking slots
    So, we could simply check that if any floor is full,
    parking slots are occupied
    To check for parking lot full, check if it's components
    are full, which is floors. 
    We can mention this verbally, no need to implement because
    of time crunch.
"""
@dataclass
class ParkingLot: 
    parkingFloors: List[ParkingFloor]

    def findAvailableSlot(self, vehicleType):

        for floor in self.parkingFloors:
            slot = floor.findAvailableSlot(vehicleType)
            if slot:
                return slot 
            
        return None 
    
    def parkVehicle(self, vehicle: Vehicle):
        vehicleType = vehicle.vehicleType
        slot = self.findAvailableSlot(vehicleType)

        if slot:
            slot.parkVehicle(vehicle)
            print(f"{vehicle.licensePlate} parked at slot number: {slot.spotNumber}.")
        else:
            print("No empty slot found!")
    
    def vacateSpot(self, spot: ParkingSlot, vehicle: Vehicle):
        if not spot:
            print("None value passed for the slot!")
            return 

        if not spot.isOccupied:
            print("Vacant spot already!")
            return
        
        if spot.vehicle != vehicle:
            print("Spot is not filled with this particular vehicle")
            return 
        
        spot.vacateSlot()
        print(f"Slot number {spot.spotNumber} has been vacated!")

"""
    In extensibility, it is majorly asked to implement multi
    floor parking lot system. In that case, we will have 
    Parking Lot -> List of parking floors
    Parking Floor -> List of parking slots
    We can use composition / builder pattern or even avoid any 
    of them.
"""


@dataclass
class ParkingFloor:
    parkingSlots: List[ParkingSlot]
    floorNumber: int

    def findAvailableSlot(self, vehicleType):

        for slot in self.parkingSlots:
            if not slot.isOccupied and slot.slotType == vehicleType:
                return slot 
            
        return None