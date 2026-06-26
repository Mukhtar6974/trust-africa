class EscrowWallet:

    def __init__(self):
        self.balance = 0

    def lock_funds(self, amount):
        self.balance += amount
        print("Funds Locked:", amount, "USDC")

    def release_funds(self):
        print("Funds Released:", self.balance, "USDC")
        self.balance = 0


escrow = EscrowWallet()

escrow.lock_funds(2000)
print("Escrow Balance:", escrow.balance, "USDC")

escrow.release_funds()
print("Escrow Balance:", escrow.balance, "USDC")