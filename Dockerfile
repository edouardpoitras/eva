FROM python:3.5-slim
RUN apt-get update && apt-get install -y git && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
ADD requirements.txt /tmp
ADD docker-compose-configs/eva.conf /etc/eva/eva.conf
ADD docker-compose-configs/configs /etc/eva/configs
RUN pip install --user -r /tmp/requirements.txt
WORKDIR /eva
CMD ["python", "/eva/serve.py"]
