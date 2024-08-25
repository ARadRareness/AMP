# TaskClock

TaskClock is a Python application designed to help users manage and track their time spent on various tasks. It's particularly effective for timeboxing multiple tasks, allowing users to set specific time limits for each activity.

## Features

- **Task Management**: Create, update, and delete tasks
- **Time Tracking**: Start and stop timers for individual tasks
- **Data Persistence**: Save and load task data to/from JSON files
- **Task Reordering**: Move tasks up or down in the list
- **Timer Adjustment**: Add or subtract time from the current task
- **Auto-reset**: Automatically reset and restart tasks when all are completed
- **Notifications**: Optional Telegram messages and desktop notifications when tasks are completed
- **Task Completion Tracking**: Mark tasks as completed and reset completed tasks


## Dependencies

TaskClock requires the amp_lib for Telegram notifications

## Configuration

The application uses a configuration file named `TaskClock.dat` to store task data. This file is automatically created in the same directory as the script.

## Usage

To run TaskClock:

```bash
python TaskClock.py
```


## License

TaskClock is licensed under the [MIT License](LICENSE).

