from workflow.run import Workflow

if __name__ == '__main__':
    Workflow(print_body=True, create_window=False).run_from_last_execution()
