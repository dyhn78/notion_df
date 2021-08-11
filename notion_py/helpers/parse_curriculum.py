lefts = []
rights = []

while True:
    string = input()
    if string == 'end':
        break
    string = string.replace('  ', ' ')
    array = string.split(' - ', 1)
    lefts.append(array[0].strip()[4:])
    try:
        rights.append(array[1].strip())
    except IndexError:
        rights.append('')

print(*lefts, '\n'*3, *rights, sep='\n')
