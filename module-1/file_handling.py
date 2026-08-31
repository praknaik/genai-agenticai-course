#example.txt

list =[
    "This is the first line \n",
    "This is the second line \n",
    "This is the third line \n",
    "This is the fourth line \n",
]

with open("employee.txt", "r") as f:
    f.writelines(list)



    # f.write("Hello World \n")
    # f.write("This is new file created using Python")

print("File written successfully")
print("-" * 70)

