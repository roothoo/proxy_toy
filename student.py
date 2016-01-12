

class Student(object):

    def __init__(self, name, age):
        self.name = name
        self.age = age

    def print_info(self):
        print '%s %d' %(self.name, self.age)