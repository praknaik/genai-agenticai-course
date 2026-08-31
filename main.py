#----------------------
# Integer
#------------------

age = 25
print("age:", age)
print("Type:", type(age))
print("Memory size:", age.__sizeof__(), "bytes")

print("-" * 70)

#----------------------
# FLOAT
#----------------------

salary = 4000.75
print("Salary:", salary)
print("Type:", type(salary))
print("Memory size:", salary.__sizeof__(), "bytes")

print("-" * 70)

#----------------------
# STRING
#----------------------

message = "Hello World!"
print("Message:", message)
print("Type:", type(message))
print("Memory size:", message.__sizeof__(), "bytes")

print("First character is :", message[0])
print("Character at index 6 is :", message[6])
print("Character at index 10 is :", message[10])

print("Length of message:", len(message))

print("-" * 70)

#----------------------
# LIST
#----------------------
numbers = [10, 20, 30, 40, 50]
print("Numbers:", numbers)
print("Type:", type(numbers))
print("Memory size:", numbers.__sizeof__(), "bytes")

print("Number at index 0 is :", numbers[2])
print("Number at index 5 is :", numbers[4])
print("Size of list is :", len(numbers))

print("-" * 70)

#----------------------
# Tuple
#----------------------

point = (5, 10, 15)
print("Point:", point)
print("Type:", type(point))

print("Memory size:", point.__sizeof__(), "bytes")

print("Point at index 2 is :", point[2])
print("Size of tuple is ", len(point))

print("-" * 70)

#----------------------
# Set
#----------------------

unique_numbers = {1, 2, 3, 3, 4, 5, 5, 5}

print("Unique numbers:", unique_numbers)

print("Type:", type(unique_numbers))
print("Memory size:", unique_numbers.__sizeof__(), "bytes")
print("Size of unique numbers is :", len(unique_numbers))
print("-" * 70)

#----------------------
# Dictionary
#----------------------

student = {
    "name" : "Rahul",
    "age" : 25,
    "courses" : [ "Python", "Agentic AI" ]
}

print("Student:", student)
print("Type:", type(student))

print("Memory size:", student.__sizeof__(), "bytes")

print("Size of student is :", len(student))

print("Student name is :", student["name"])
print("Student age is :", student["age"])
print("Student courses is :", student["courses"])
print("2nd course :", student["courses"][1])

student["mobile"] = 978927389

print("Student updated with mobile number :", student)







