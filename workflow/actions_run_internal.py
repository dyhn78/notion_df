from workflow.actions import get_actions
from workflow.actions_exec import execute_from_last_success

if __name__ == '__main__':
    execute_from_last_success(actions=get_actions(), update_last_success_time=True)
