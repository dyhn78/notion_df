from app.action.__routine__ import routine_action

if __name__ == "__main__":
    routine_action.run_from_last_success(update_last_success_time=True)
