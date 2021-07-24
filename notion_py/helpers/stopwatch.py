import time

start_time = time.time()


def stopwatch(comments: str) -> None:
    seconds = round(time.time() - start_time, 3)
    minutes = int(seconds // 60)
    second_str = '%6.3f' % (seconds - minutes * 60)
    minute_str = '%3d' % minutes
    if minutes:
        print(f'{minute_str}분 {second_str}초| {comments}')
    else:
        print(f'{second_str}초| {comments}')
