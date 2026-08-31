class Car:
    def __init__(self, color, brand, model, speed):
        self.color = color
        self.brand = brand
        self.model = model
        self.speed = speed

    def display(self):
        print(self.color)
        print(self.brand)
        print(self.model)

    def show(self):
        print("Inside show")


# Object creation statement
honda_city_car = Car("blue", "Honda", "City", "180")
print(" My car brand is : " , honda_city_car.brand)
print(" My car model is : " , honda_city_car.model)
print(" My car speed is : " , honda_city_car.speed)
honda_city_car.display()

hyundai_city_car = Car("red", "Hyundai", "Verna", "200")
print(" My car brand is : " , hyundai_city_car.brand)
print(" My car model is : " , hyundai_city_car.model)
print(" My car speed is : " , hyundai_city_car.speed)
hyundai_city_car.display()

print("-" * 70)

#super class, base class , parent class
class Person:
    def __init__(self, name, age):
        print("Inside __init__ of super class")
        self.name = name
        self.age = age

#sub class, derived class, child class
class Employee(Person):
    def __init__(self, first_name ):
        print("Inside __init__ of sub class")
        self.first = first_name
        super().__init__(first_name, 25)

    def show(self):
        print("Inside show")
        print(self.first)

emp = Employee("Ram")
print(emp.age)
#emp.show()
#print(emp.first)







