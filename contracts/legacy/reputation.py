class Reputation:

    def __init__(self, name):
        self.name = name
        self.score = 50

    def increase(self, points):
        self.score += points

    def decrease(self, points):
        self.score -= points

    def show(self):
        print("User:", self.name)
        print("Trust Score:", self.score)


buyer = Reputation("Amina")

buyer.show()

print()

buyer.increase(20)

buyer.show()

print()

buyer.decrease(10)

buyer.show()