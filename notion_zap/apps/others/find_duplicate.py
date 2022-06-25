strings = set()

while True:
    string = input()
    if string in strings:
        raise ValueError(string)
    strings.add(string)
