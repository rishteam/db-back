from .course import get_currnet_course_list

def test(passwd):
    print(get_currnet_course_list('406262515', passwd))

if __name__ == '__main__':
    test(input('passwd: '))