class A:
    ct = 2

    def __init__(self):
        self.dt = self.ct + 2


class B(A):
    ct = 3


b = B()
print(b.dt)
