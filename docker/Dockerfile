FROM python:3.9-slim 
RUN python -m venv /venv
RUN mkdir /app
COPY serve requirements.txt README.txt *.py /app/
WORKDIR /app
RUN /venv/bin/python -m pip install -r requirements.txt
ENV PATH="/venv/bin:${PATH}"
CMD ["serve"]
