# -*- coding: utf-8 -*-
import server
from student import *
from Animal import *

def main():
    # server.socket_server_test()
    stu1 = Student('Jack', 22)
    stu1.print_info()

    dog = Dog()
    dog.run()

if __name__ == '__main__':
    main()