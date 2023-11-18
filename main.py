from app import app
import schedule
from helper import update_data
import time
from multiprocessing import Process

# Flag to ensure the scheduler is started only once
scheduler_started = False

# Define a function to run the scheduled task
def run_scheduler():
    schedule.every(15).seconds.do(update_data)
    while True:
        schedule.run_pending()
        time.sleep(15)

# Start the scheduler in a separate process
if __name__ == '__main__':
    if not scheduler_started:
        scheduler_process = Process(target=run_scheduler)
        scheduler_process.start()
        scheduler_started = True
    app.run(debug=True, host='0.0.0.0')
