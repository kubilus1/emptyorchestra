FROM ubuntu

RUN apt-get update && apt-get install -y python python-pip
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

EXPOSE 5000

CMD python eo_web.py
