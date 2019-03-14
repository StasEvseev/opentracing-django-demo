FROM python:3
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install --index-url https://artifacts.kpn.org/api/pypi/pypi/simple --trusted-host artifacts.kpn.org -r requirements.txt
COPY . /code/
