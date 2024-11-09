FROM python:3.11-slim-buster

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

WORKDIR /app

COPY . /alcopt
RUN pip install /alcopt

# CMD [ "python", "alcopt/run_app.py" ]
# CMD ["sleep", "infinity"]