from workflow.routine.routine import WorkflowAction

if __name__ == '__main__':
    WorkflowAction.run_from_last_success(update_last_success_time=True)
