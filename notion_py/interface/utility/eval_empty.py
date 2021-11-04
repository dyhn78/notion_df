def eval_empty(value):
    if type(value) in [list, dict]:
        return bool(value)
    else:
        falsey = ['', '.', '-', '0', '1', 'None', 'False']
        return str(value) in falsey
