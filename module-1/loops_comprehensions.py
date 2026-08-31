print("Hello")

for item in range(100):
    print(item)

text = "Python"
for char in text:
    print(char)

cities = ["Delhi", "Mumbai", "Bangalore"]
for index, city in enumerate(cities):
    print(f"{index} and its corresponding city is {city}")

student = {"name" : "Rahul", "age" : 25, "course" : "Python"}
for key, value in student.items():
    print("Key :", key, "Value:", value)



#------------------------------------
#WHILE loop example
#------------------------------------
#tank capacity = 100 ml

water_level = 0
print("Tank is empty")
while water_level < 100:
    print("Filling water tank")
    water_level = water_level + 20
print("Tank is fully filled")


pin = input("Please Enter salary : ")
print("Entered PIN is ", type(float(pin)))

correct_pin = 1234
pin = 0

while pin != correct_pin:
    pin = input("Enter a pin ")
    pin = int(pin)

print("PIN accepted!")

list = [1,2,3,4,5]
squares = []

for number in list:
    squares.append(number*number)

print(squares)

print("Comprehension ===========================")
squares_comp = [number * number for number in list]
print(squares_comp)













