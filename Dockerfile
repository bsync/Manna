#FROM amazon/aws-eb-python:3.4.2-onbuild-3.5.1
#FROM frolvlad/alpine-python2
#FROM alpython:v2_vim
FROM alpython:v4_cmd
ADD . /code
RUN apk --update add vim ffmpeg
RUN pip install -r /code/requirements.txt
EXPOSE 5000
WORKDIR /code 
CMD FLASK_APP=manna.py FLASK_DEBUG=1 flask run 
