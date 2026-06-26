class TradeHistory:

    def __init__(self):
        self.records = []

    def add_trade(self, trade_id, buyer, seller, amount):
        self.records.append({
            "trade_id": trade_id,
            "buyer": buyer,
            "seller": seller,
            "amount": amount
        })

    def show_history(self):
        for trade in self.records:
            print()
            print("Trade ID:", trade["trade_id"])
            print("Buyer:", trade["buyer"])
            print("Seller:", trade["seller"])
            print("Amount:", trade["amount"])


history = TradeHistory()

history.add_trade(
    "TRADE001",
    "Amina",
    "Kwame",
    2000
)

history.add_trade(
    "TRADE002",
    "John",
    "Fatima",
    3500
)

history.show_history()