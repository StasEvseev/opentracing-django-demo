FROM python:3.6
RUN apt-get update && apt-get install -y libsasl2-dev python-dev libldap2-dev libssl-dev
ENV PYTHONUNBUFFERED 1

RUN mkdir -p /opt/django
WORKDIR /opt/django

COPY requirements.txt /opt/django/
RUN pip install --index-url https://artifacts.kpn.org/api/pypi/pypi/simple --trusted-host artifacts.kpn.org -r requirements.txt
RUN pip install uwsgi
RUN pip install --index-url http://host.docker.internal:8080/simple/ --trusted-host host.docker.internal service-base==5.1.0  django-de-core==5.3.2

ENTRYPOINT ["/usr/local/bin/uwsgi", "/etc/uwsgi.ini"]
