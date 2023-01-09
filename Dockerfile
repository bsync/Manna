FROM python:3.9-slim
RUN apt-get update; apt-get install -y ffmpeg
RUN mkdir /app /catalog
WORKDIR /app
COPY serve README.txt pyproject.toml setup.cfg /app/
COPY manna /app/manna
RUN python -m pip install -e .
CMD ["/app/serve"]
