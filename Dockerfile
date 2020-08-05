FROM python:3.7-alpine as base
FROM base as builder
RUN mkdir /install
WORKDIR /install
COPY requirements.txt /requirements.txt
RUN apk add gcc musl-dev curl-dev python3-dev libressl-dev libffi-dev
RUN pip install --user -r /requirements.txt

FROM base
RUN apk add ffmpeg libcurl
COPY --from=builder /root/.local /usr/local
#dateutil package doesn't seem to honor prefix so reinstall it here
RUN pip install python-dateutil  
WORKDIR /app
COPY *.py serve ./
COPY static /app/static
CMD [ "./serve" ]
