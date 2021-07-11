import time

start_time = time.time()


def stopwatch(comments: str):
    elapsed_time = f'{comments}; {round((time.time() - start_time) * 1000)} 밀리초'
    print(elapsed_time)

