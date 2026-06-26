class Escrow:
    def __init__(self, amount):
        self.amount = amount
        self.locked = True

    def release_funds(self):
        self.locked = False
        print("Funds Released:", self.amount)

    def refund(self):
        self.locked = False
        print("Funds Refunded:", self.amount)