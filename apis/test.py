from . import schedule as sc

a = sc.CoursePeriod('DN', 'DN')
b = sc.CoursePeriod('D2', 'DN')

print(a in b)
print(b in a)
