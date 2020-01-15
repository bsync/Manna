FROM python:3.7-alpine as base
FROM base as builder
RUN mkdir /install
WORKDIR /install
COPY requirements.txt /requirements.txt
RUN pip install --install-option="--prefix=/install" -r /requirements.txt

FROM base
COPY --from=builder /install /usr/local
#dateutil package doesn't seem to honor prefix so reinstall it here
RUN pip install python-dateutil  
WORKDIR /app
COPY src/ .
ENTRYPOINT [ "./serve" ]
