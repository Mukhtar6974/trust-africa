from backend.wallet import Wallet
from backend.escrow import EscrowWallet

buyer = Wallet("Amina", 5000)
seller = Wallet("Kwame", 1000)
escrow = EscrowWallet()

print("===== TRUST AFRICA TRADE =====")
print()

buyer.show()
print()

if buyer.send(2000):
    escrow.lock_funds(2000)

print()
print("AI Review Complete")
print("Evidence Approved")
print()

escrow.release_funds()
seller.deposit(2000)

print()
print("===== FINAL BALANCES =====")
print()

buyer.show()
print()
seller.show()