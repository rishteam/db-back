from . import course

a = course.CoursePeriod('D1', 'E0')
b = course.CoursePeriod('D5', 'D7')

print(b in a)
print(a in b)