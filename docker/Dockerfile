FROM python:3.9-slim
RUN apt-get update; apt-get install -y ffmpeg
RUN python -m venv /venv
RUN mkdir /app
ADD manna /app/manna
COPY serve README.txt pyproject.toml setup.cfg /app/
WORKDIR /app
RUN /venv/bin/python -m pip install -e .
ENV PATH="/venv/bin:${PATH}"
CMD ["serve"]
