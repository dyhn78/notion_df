from workflow.actions import get_action

if __name__ == '__main__':
    get_action().run_from_last_success(update_last_success_time=True)
