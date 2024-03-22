from workflow.routine.action import routine

if __name__ == '__main__':
    routine.run_from_last_success(update_last_success_time=True)
