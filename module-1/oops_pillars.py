# Encaptulation

class BankAccount:
    def __init__(self, balance):
        self.balance = balance

    def deposit(self, amount):
        self.balance += amount

    def withdraw(self, amount):
        self.balance -= amount

    def display(self):
        print(self.balance)


account = BankAccount(100)
print("Balance is : ", account.balance)

account.deposit(100)
print("Balance is : ", account.balance)

account.withdraw(50)
print("Balance is : ", account.balance)



#Abstraction

class Car:
    def start(self):
        self.start_engine()
        print("car started !!!")

    def start_engine(self):
        print("engine started !!!")

car = Car()
#car.start()

#parent class, base class
class Animal:
    def eat(self):
        print(" eating ")

    def sleep(self):
        print(" sleeping ")
#child class, derived class
class Dog(Animal):
    def bark(self):
        print(" barking ")
#child class, derived class
class Cat(Animal):
    def meow(self):
        print(" meowing ")

animal = Dog()
animal.eat()
animal.sleep()
animal.bark()
print("-" * 70)
animal = Cat()
animal.eat()
animal.sleep()
animal.meow()

#polymorphim

class Dog:
    def sound(self):
        print(" barking ")

class Cat:
    def sound(self):
        print(" meowing ")


animal = [Dog(), Cat()]
for a in animal:
    a.sound()