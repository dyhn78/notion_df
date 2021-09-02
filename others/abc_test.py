class A:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return f'A({self.value})'


array = [A(2), A(3)]
c = A(4)
array.append(c)
print(array)
del c
print(array)
