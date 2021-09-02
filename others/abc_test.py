class Cls1:
    def __init__(self):
        self.a = 2

class Cls2:
    def __init__(self):
        self.b = 3

class Cls3(Cls1, Cls2):
    def __init__(self):
        print(super())
        super().__init__()

inst3 = Cls3()
print(inst3.b)
print(inst3.a)
