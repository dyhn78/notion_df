import time

start_time = time.time()


def stopwatch(comments: str):
    seconds = round(time.time() - start_time, 3)
    minutes = int(seconds // 60)
    seconds = round(seconds - minutes * 60, 3)
    second_str = f'{seconds} 초; {comments}'
    if minutes:
        minute_str = f'{minutes} 분'
        print(f'{minute_str} {second_str}')
    else:
        print(second_str)

