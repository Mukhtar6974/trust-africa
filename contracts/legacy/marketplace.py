class Listing:

    def __init__(self, seller, product, price):
        self.seller = seller
        self.product = product
        self.price = price
        self.active = True

    def display(self):
        print("Seller:", self.seller)
        print("Product:", self.product)
        print("Price:", self.price)
        print("Active:", self.active)

    def deactivate(self):
        self.active = False


listing = Listing(
    "Kwame",
    "500 textile materials",
    2000
)

listing.display()

print()

listing.deactivate()

listing.display()