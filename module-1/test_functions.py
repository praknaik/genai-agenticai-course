#creating and calling a function

#creating a function
def add(a, b):
    res = a + b
    return res

def  subtract(a, b):
    res = a - b
    return res

def multiply(a, b):
    res = a * b
    return res

def divide(a, b):
    res = a / b
    return res


def greeting(message):
    return message

def get_stat(marks_list):
    total = sum(marks_list)
    length = len(marks_list)
    average = total / length
    return total, length, average


if __name__ == "__main__":

    #calling of a function
    returned_message = greeting("Welcome to Python! Basic Calculator")
    print(returned_message)
    print("-" * 70)
    #calling of a function to add two numbers
    result_of_addition = add(20, 30)
    print("Addition : ", result_of_addition)

    result_of_subtraction = subtract(40, 30)
    print("Subtraction :", result_of_subtraction)

    result_of_multiplication = multiply(20, 30)
    print("Multiplication : ", result_of_multiplication)

    result_of_division = divide(40, 30)
    print("Division : ", result_of_division)

    print("-" * 50)

    list = [60, 70, 80, 60, 60, 70, 80, 60]
    # calling get_stat function with list of marks as input
    total, length, average = get_stat(list)
    print("Total: ", total)
    print("Length: ", length)
    print("Average: ", average)

    print("-" * 50)

    list1 = [60, 70, 80, 60]
    # calling get_stat function with list of marks as input
    total, length, average = get_stat(list1)
    print("Total: ", total)
    print("Length: ", length)
    print("Average: ", average)













