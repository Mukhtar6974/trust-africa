class Wallet:

    def __init__(self, owner, balance):
        self.owner = owner
        self.balance = balance

    def deposit(self, amount):
        self.balance += amount

    def send(self, amount):
        if amount <= self.balance:
            self.balance -= amount
            return True
        return False

    def show(self):
        print("Owner:", self.owner)
        print("Balance:", self.balance, "USDC")


buyer_wallet = Wallet("Amina", 5000)
seller_wallet = Wallet("Kwame", 1000)

buyer_wallet.show()
print()

if buyer_wallet.send(2000):
    seller_wallet.deposit(2000)

buyer_wallet.show()
print()
seller_wallet.show()