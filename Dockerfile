FROM ubuntu:14.04

# Update packages and install pip
RUN DEBIAN_FRONTEND=noninteractive apt-get update -y && apt-get -y install python python-pip python-dev libpq-dev libffi-dev

# Set WORKDIR to /src
WORKDIR /src

# Add and install Python modules
ADD requirements.txt /src/requirements.txt
RUN pip install -r requirements.txt

# Bundle app source
ADD . /src

# Install main module
RUN python setup.py install

# Expose
EXPOSE 5000
