from pydantic import BaseModel


class Student:
    def __init__(self, name, age ):
        self.name = name
        self.age = age

    def __str__(self):
        return f"{self.name} {self.age}"

    def __eq__(self, other):
        return self.name == other.name and self.age == other.age


s1 = Student("Ram", 22)
s2 = Student("Priya", 22)

print(s1)
print(s2)

print(s1 == s2)

from dataclasses import dataclass

@dataclass
class Student:
    name: str
    age: int

s3 = Student("Ram", 22)
s4 = Student("Ram", 22)

print(s3)
print(s4)

print(s3 == s4)

from pydantic import BaseModel, Field, EmailStr
class Student(BaseModel):
    name: str = Field(min_length=3, max_length=10)
    age: int = Field(min_length=3, max_length=3)
    email: EmailStr