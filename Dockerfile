FROM python:3.11-slim-buster

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6 git -y

WORKDIR /app

COPY . /alcopt

RUN pip install -r /alcopt/requirements.txt
RUN pip install /alcopt

CMD streamlit run /alcopt/alcopt/app/Home.py --server.port=$PORT --server.address=0.0.0.0