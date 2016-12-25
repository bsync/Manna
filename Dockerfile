#FROM amazon/aws-eb-python:3.4.2-onbuild-3.5.1
FROM frolvlad/alpine-python2
ADD . /code
RUN pip install -r /code/requirements.txt
