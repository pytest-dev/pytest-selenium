FROM python:3.10-slim-buster

WORKDIR /usr/src/app

ENV FLASK_APP=webserver.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=80

RUN python -m pip install --upgrade pip && \
    pip install flask

COPY webserver.py .

ENTRYPOINT ["flask"]
CMD ["run"]
