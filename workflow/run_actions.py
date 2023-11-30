from workflow.actions import actions
from workflow.core.action import run_from_last_success

if __name__ == '__main__':
    # TODO: add click command
    print(f'{"#" * 5} Start.')
    new_record = run_from_last_success(actions=actions, print_body=True, update_last_success_time=True)
    print(f'{"#" * 5} {"Done." if new_record else "No new record."}')
