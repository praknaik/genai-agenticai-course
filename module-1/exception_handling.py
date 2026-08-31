
try:
    print("hello world")
    x = 10/0
    print("in try block after x is calculated")
except ZeroDivisionError:
    print("ERROR : Can not divide by ZERO")
else:
    print("No ERROR", x)
finally:
    print("FINISHED")


#Custom Exception:

class InvalidAgeError(Exception):
    pass

class InsufficientFundError(Exception):
    pass


def register_user(name, age):
    if age < 18:
        raise InvalidAgeError(f"User {name} must be at-leat years old")
    print(f"User {name} registered successfully")

def withdraw(amount):
    balance = 100
    if balance < amount :
        raise InsufficientFundError("Insufficient funds")
    balance = balance - amount
    print("Remaining Balance is : ", balance)

try:
    #register_user("john", 16)
    withdraw(50)
except InsufficientFundError as e:
    print("Insufficient Funds Error \n", e)