def eval_empty(value):
    if type(value) in [bool, list, dict]:
        return bool(value)
    else:
        return str(value) in ['', '.', '-', '0', '1']