from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import List, Dict


@dataclass
class User:
    id: int 
    name: str 
    email: str 


@dataclass
class UserManager:
    users: Dict[int, User] = field(default_factory=dict)
    
    # To-do : Add singleton pattern so only instance of usermanager exists

    def getUser(self, id):
        if not self.users.get(id):
            raise Exception("Invalid user id!")
        return self.users.get(id)


class Split(ABC):
    @abstractmethod
    def split(self, amount: float, participants: List[User], splitDetails: Dict[int, float]) -> Dict[int, float]:
        pass 


class EqualSplit(Split):
    def split(self, amount: float, participants: List[User], splitDetails: Dict[int, float]):
        totalSplitShare = dict()
        numOfParticipants = len(participants)

        for participant in participants:
            splitShare = amount / numOfParticipants
            totalSplitShare[participant.id] = splitShare

        return totalSplitShare


class PercentageSplit(Split):
    def split(self, amount: float, participants: List[User], splitDetails: Dict[int, float]) -> Dict[int, float]:
        # TO-DO: Add implementation for the percentage based split
        return super().split(amount, participants, splitDetails)


class SplitFactory():
    @staticmethod
    def createSplit(splitType: str):
        splitTypes = {
            "equal": EqualSplit,
            "percentage": PercentageSplit
        }

        split = splitTypes.get(splitType, None)

        if not split:
            raise Exception("Invalid split type!")
        
        return split()


@dataclass
class UserPair:
    payer: User 
    payee: User 


class Observer(ABC):
    @abstractmethod
    def onExpenseUpdate(self, expense):
        pass 

    @abstractmethod
    def onExpenseAdded(self, expense):
        pass 


@dataclass
class BalanceSheet(Observer):
    balances: Dict[UserPair, float]
    userManager: UserManager = field(default_factory = UserManager)

    def onExpenseUpdate(self, expense: Expense):
        self.updateBalances(expense)

    def onExpenseAdded(self, expense):
        self.updateBalances(expense)

    def updateBalances(self, expense: Expense):
        creditor = expense.payer
        splitShares = expense.shares

        for userId, share in splitShares.items():
            debtor = self.userManager.getUser(userId)
            if debtor is not None and debtor != creditor:
                userPair = UserPair(debtor, creditor)
                currBalance = self.balances.get(userPair, 0.0)
                self.balances[userPair] = currBalance + share 
    
    # Get the net balance between two users
    # We will return the amount user1 owes user2 (negative if user2 owes user1)
    def getBalance(self, user1: User, user2:User):
        pair1 = UserPair(user1, user2)
        pair2 = UserPair(user2, user1)

        balance1 = self.balances.get(pair1, 0.0)
        balance2 = self.balances.get(pair2, 0.0)

        return balance1 - balance2
    
    def getTotalBalance(self, user: User):

        total = 0

        for userPair, amount in self.balances.items():
            creditor = userPair.payee
            debitor = userPair.payer

            if creditor == user:
                total += amount 
            
            if debitor == user:
                total -= amount 

        return total 


    def calculateNetBalances(self):
        netBalances = dict() # user -> float

        for userPair, amount in self.balances.items():
            debtor = userPair.payer
            creditor = userPair.payee

            if debtor in netBalances:
                netBalances[debtor] -= amount
            else:
                netBalances[debtor] = -amount 

            if creditor in netBalances:
                netBalances[creditor] += amount
            else: 
                netBalances[creditor] = amount 

        return netBalances

    def getSimplifiedSettlements(self):
        """
            - Simplifies the balances into a list of transactions to settle all the debts
            - Simple and straightforward implementation of the problem, may provide inaccurate results
            - return list of transactions to settle all the debts
        """
        # Step 1: Calculate net balance for each user
        netBalances = self.calculateNetBalances()
        
        # Step 2: separate users into debtors and creditors
        debtors = list()
        creditors = list()
        for user, bal in netBalances.items():
            if bal > 0:
                creditors.append(user)
            if bal < 0:
                debtors.append(user) 
        

        # Step 3: Match creditors and debtors to create Transactions
        transactions : List[Transaction] = list()
        creditorIndex, debtorIndex = 0, 0

        while creditorIndex < len(creditors) and debtorIndex < len(debtors):
            creditor = creditors[creditorIndex]
            debtor = debtors[debtorIndex]

            creditorBal = netBalances[creditor]
            debtorBal = netBalances[debtor]

            transferAmt = min(creditorBal, abs(debtorBal))

            netBalances[creditor] -= transferAmt
            netBalances[debtor] += transferAmt

            if abs(netBalances[creditor]) < 0.001:
                creditorIndex += 1
            
            if abs(netBalances[debtor]) < 0.001:
                debtorIndex += 1

            transaction = Transaction(creditor, debtor, transferAmt)
            transactions.append(transaction)
        
        return transactions
    

    def getSubOptimalMinimumSettlements(self):
        # Step 1: Calculate net balance for each user
        netBalances = self.calculateNetBalances()

        # Step 2: Find list of the balances (credits or debts)
        balancesList = [ bal for bal in netBalances.values() ]

        return self.subOptimalDFS(0, balancesList, len(balancesList))
    
    def subOptimalDFS(self, idx, balances, n) -> int:
        """
            T.C. -> O(n-1)!
            At first call, I have n-1 options, similarly on next I will have n-2 options ... in each call, we are moving the index by 1, and trying to settle the amount by future creditors
            T.C. -> (n-1)*(n-2)*...(1) -> O(n-1)! -> O(n)!
            Since, it follows backtracking it will always help us in computing the correct solution, as we are keeping the cost angle in scope always.
        """
        while idx < n and balances[idx] == 0:
            idx += 1

        if idx == n:
            return 0

        currBal = balances[idx]

        cost = float('inf')
        for nextidx in range(idx + 1, n):
            nextBal = balances[nextidx]

            if nextBal * currBal < 0:

                balances[nextidx] = nextBal + currBal
                cost = min(cost, 1 + self.subOptimalDFS(idx+1, balances, n))
                balances[nextidx] = nextBal

        return int(cost) 


    def getOptimalMinimumSettlements(self):
        netBalances = self.calculateNetBalances()

        balancesList = [ bal for bal in netBalances.values() ]
        n = len(balancesList)
        mask = 1 << n
        dp = [-1 for _ in range(1<<n)]

        return n - self.optimalDP(balancesList, mask, dp)
    
    def sumOfMask(self, mask, balances):
        sum = 0
        for idx in range(len(balances)):
            if mask & (1 << idx):
                sum += balances[idx]

        return sum  

    def optimalDP(self, balances, mask, dp) -> int:
        if mask == 0:
            return 0
        
        if dp[mask] != -1:
            return dp[mask]

        n = len(balances)
        
        maxSubsets = 0

        for submask in range(1, (1 << n)):
            # check if submask (subset) is a part of mask (set)
            if mask & submask == submask and abs(self.sumOfMask(submask, balances)) < 0.0001:
                maxSubsets = max(maxSubsets, 1 + self.optimalDP(balances, mask ^ submask, dp))

        dp[mask] = maxSubsets
        return maxSubsets

@dataclass
class Expense:
    id: int 
    description: str 
    amount: float 
    payer: User 
    participants: List[User]
    shares: Dict[int, float]
    splitType: Split


@dataclass
class ExpenseManager:
    expenses: List[Expense]
    observers: List[Observer]

    def addExpense(self, expense):
        self.expenses.append(expense)
        self.onExpenseAdded(expense)
    
    def onExpenseAdded(self, expense):
        for observer in self.observers:
            observer.onExpenseAdded(expense)

    


@dataclass
class Transaction:
    payee: User 
    payer: User 
    amount: float 


