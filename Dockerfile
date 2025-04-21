FROM python:3.11-slim-buster

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6 git -y

COPY . /app
WORKDIR /app

RUN pip install -r /app/requirements.txt
RUN pip install -e /app

# CMD [ "python", "app/run_app.py" ]
# CMD ["sleep", "infinity"]