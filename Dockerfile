FROM python:3.11-slim-buster

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6 git -y

COPY . /app
WORKDIR /app

RUN pip install -r /app/requirements.txt
RUN pip install -e /app

CMD streamlit run /app/alcopt/app/Home.py --server.port=$PORT --server.address=0.0.0.0
