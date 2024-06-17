from newsportal.news.celery import Celery


app = Celery('tasks', broker='redis://:MakYdMlktWB2KncJp7qsJFtNfL0cGe7O@redis-16702.c321.us-east-1-2.ec2.redns.redis-cloud.com:16702',
             backend='redis://:MakYdMlktWB2KncJp7qsJFtNfL0cGe7O@redis-16702.c321.us-east-1-2.ec2.redns.redis-cloud.com:16702')

@app.task
def add(x, y):
    return x + y
venv\Scripts\activate