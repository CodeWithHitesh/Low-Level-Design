from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class User:
    """Registered user in the system."""
    id: int 
    name: str 
    email: str 


@dataclass
class UserManager:
    """Registry of all users in the system."""
    users: Dict[int, User] = field(default_factory=dict)

    def getUser(self, id: int) -> User:
        if not self.users.get(id):
            raise ValueError(f"User with id {id} not found")
        return self.users.get(id)


class Split(ABC):
    """Abstract strategy for splitting an expense among participants."""

    @abstractmethod
    def split(self, amount: float, participants: List[User],
              split_details: Dict[int, float]) -> Dict[int, float]:
        pass


class EqualSplit(Split):
    """Splits the amount equally among all participants."""

    def split(self, amount: float, participants: List[User],
              split_details: Dict[int, float]) -> Dict[int, float]:
        total_split_share = dict()
        num_of_participants = len(participants)

        for participant in participants:
            split_share = amount / num_of_participants
            total_split_share[participant.id] = split_share

        return total_split_share


class PercentageSplit(Split):
    """Splits the amount by user-defined percentages."""

    def split(self, amount: float, participants: List[User],
              split_details: Dict[int, float]) -> Dict[int, float]:
        total_split_share = dict()
        for participant in participants:
            percentage = split_details.get(participant.id, 0.0)
            total_split_share[participant.id] = amount * (percentage / 100)
        return total_split_share


class SplitFactory:
    """Creates the appropriate Split strategy by type name."""

    @staticmethod
    def create(split_type: str) -> Split:
        split_types = {
            "equal": EqualSplit,
            "percentage": PercentageSplit,
        }
        split_cls = split_types.get(split_type)
        if not split_cls:
            raise ValueError(f"Invalid split type: {split_type}")
        return split_cls()


@dataclass
class UserPair:
    """Directional pair representing a debtor-creditor relationship."""
    payer: User 
    payee: User 


class Observer(ABC):
    """Observer interface for expense events."""

    @abstractmethod
    def onExpenseUpdate(self, expense: 'Expense') -> None:
        pass

    @abstractmethod
    def onExpenseAdded(self, expense: 'Expense') -> None:
        pass


@dataclass
class BalanceSheet(Observer):
    """Tracks pairwise balances and computes simplified settlements."""
    balances: Dict[UserPair, float]
    user_manager: UserManager = field(default_factory=UserManager)

    def onExpenseUpdate(self, expense: 'Expense') -> None:
        self.updateBalances(expense)

    def onExpenseAdded(self, expense: 'Expense') -> None:
        self.updateBalances(expense)

    def updateBalances(self, expense: 'Expense') -> None:
        creditor = expense.payer
        split_shares = expense.shares

        for user_id, share in split_shares.items():
            debtor = self.user_manager.getUser(user_id)
            if debtor is not None and debtor != creditor:
                user_pair = UserPair(debtor, creditor)
                curr_balance = self.balances.get(user_pair, 0.0)
                self.balances[user_pair] = curr_balance + share

    def getBalance(self, user1: User, user2: User) -> float:
        """Return the amount user1 owes user2 (negative if user2 owes user1)."""
        pair1 = UserPair(user1, user2)
        pair2 = UserPair(user2, user1)

        balance1 = self.balances.get(pair1, 0.0)
        balance2 = self.balances.get(pair2, 0.0)

        return balance1 - balance2

    def getTotalBalance(self, user: User) -> float:
        total = 0

        for user_pair, amount in self.balances.items():
            creditor = user_pair.payee
            debitor = user_pair.payer

            if creditor == user:
                total += amount

            if debitor == user:
                total -= amount

        return total

    def calculateNetBalances(self) -> Dict[User, float]:
        net_balances: Dict[User, float] = dict()

        for user_pair, amount in self.balances.items():
            debtor = user_pair.payer
            creditor = user_pair.payee

            if debtor in net_balances:
                net_balances[debtor] -= amount
            else:
                net_balances[debtor] = -amount

            if creditor in net_balances:
                net_balances[creditor] += amount
            else:
                net_balances[creditor] = amount

        return net_balances

    def getSimplifiedSettlements(self) -> List['Transaction']:
        """Greedy matching of debtors and creditors into settlement transactions."""
        net_balances = self.calculateNetBalances()

        debtors = list()
        creditors = list()
        for user, bal in net_balances.items():
            if bal > 0:
                creditors.append(user)
            if bal < 0:
                debtors.append(user)

        transactions: List[Transaction] = list()
        creditor_index, debtor_index = 0, 0

        while creditor_index < len(creditors) and debtor_index < len(debtors):
            creditor = creditors[creditor_index]
            debtor = debtors[debtor_index]

            creditor_bal = net_balances[creditor]
            debtor_bal = net_balances[debtor]

            transfer_amt = min(creditor_bal, abs(debtor_bal))

            net_balances[creditor] -= transfer_amt
            net_balances[debtor] += transfer_amt

            if abs(net_balances[creditor]) < 0.001:
                creditor_index += 1

            if abs(net_balances[debtor]) < 0.001:
                debtor_index += 1

            transaction = Transaction(creditor, debtor, transfer_amt)
            transactions.append(transaction)

        return transactions

    def getSubOptimalMinimumSettlements(self) -> int:
        """Backtracking approach — O(n!) worst case."""
        net_balances = self.calculateNetBalances()
        balances_list = [bal for bal in net_balances.values()]
        return self.subOptimalDFS(0, balances_list, len(balances_list))

    def subOptimalDFS(self, idx: int, balances: List[float], n: int) -> int:
        """
        T.C. -> O((n-1)!) backtracking over all possible settlement orderings.
        """
        while idx < n and balances[idx] == 0:
            idx += 1

        if idx == n:
            return 0

        curr_bal = balances[idx]

        cost = float('inf')
        for next_idx in range(idx + 1, n):
            next_bal = balances[next_idx]

            if next_bal * curr_bal < 0:
                balances[next_idx] = next_bal + curr_bal
                cost = min(cost, 1 + self.subOptimalDFS(idx + 1, balances, n))
                balances[next_idx] = next_bal

        return int(cost)

    def getOptimalMinimumSettlements(self) -> int:
        """Bitmask DP — finds maximum number of zero-sum subsets."""
        net_balances = self.calculateNetBalances()
        balances_list = [bal for bal in net_balances.values()]
        n = len(balances_list)
        mask = 1 << n
        dp = [-1 for _ in range(1 << n)]
        return n - self.optimalDP(balances_list, mask, dp)

    def sumOfMask(self, mask: int, balances: List[float]) -> float:
        total = 0
        for idx in range(len(balances)):
            if mask & (1 << idx):
                total += balances[idx]
        return total

    def optimalDP(self, balances: List[float], mask: int, dp: List[int]) -> int:
        if mask == 0:
            return 0

        if dp[mask] != -1:
            return dp[mask]

        n = len(balances)
        max_subsets = 0

        for submask in range(1, (1 << n)):
            if mask & submask == submask and abs(self.sumOfMask(submask, balances)) < 0.0001:
                max_subsets = max(max_subsets, 1 + self.optimalDP(balances, mask ^ submask, dp))

        dp[mask] = max_subsets
        return max_subsets

@dataclass
class Expense:
    """A single expense record with payer, participants, and computed shares."""
    id: int
    description: str
    amount: float
    payer: User
    participants: List[User]
    shares: Dict[int, float]
    split_type: Split


# ─── Orchestrator ────────────────────────────────────────────

@dataclass
class ExpenseManager:
    """Manages expenses and notifies observers on changes."""
    expenses: List[Expense]
    observers: List[Observer]

    def addExpense(self, expense: Expense) -> None:
        self.expenses.append(expense)
        self.onExpenseAdded(expense)

    def onExpenseAdded(self, expense: Expense) -> None:
        for observer in self.observers:
            observer.onExpenseAdded(expense)


@dataclass
class Transaction:
    """Settlement transaction from payer to payee."""
    payee: User
    payer: User
    amount: float


# ─── Demo ───────────────────────────────────────────────────────

if __name__ == "__main__":
    alice = User(1, "Alice", "alice@test.com")
    bob = User(2, "Bob", "bob@test.com")
    charlie = User(3, "Charlie", "charlie@test.com")

    user_mgr = UserManager(users={1: alice, 2: bob, 3: charlie})
    balance_sheet = BalanceSheet(balances=dict(), user_manager=user_mgr)

    split = SplitFactory.create("equal")
    participants = [alice, bob, charlie]
    shares = split.split(300.0, participants, {})

    expense = Expense(1, "Dinner", 300.0, alice, participants, shares, split)

    manager = ExpenseManager(expenses=[], observers=[balance_sheet])
    manager.addExpense(expense)

    print(f"Bob owes Alice: {balance_sheet.getBalance(bob, alice)}")
    print(f"Charlie owes Alice: {balance_sheet.getBalance(charlie, alice)}")

    settlements = balance_sheet.getSimplifiedSettlements()
    for t in settlements:
        print(f"{t.payer.name} pays {t.payee.name}: {t.amount}")

