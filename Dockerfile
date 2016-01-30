FROM ubuntu:14.04

# Create limited user for Celery
RUN groupadd user && useradd --create-home --home-dir /home/user -g user user

# Set WORKDIR to /home/user
WORKDIR /home/user

# Update packages and install pip
RUN DEBIAN_FRONTEND=noninteractive apt-get update -y && apt-get -y install python python-pip python-dev libpq-dev libffi-dev

# Add and install Python modules
ADD requirements.txt /home/user/requirements.txt
RUN pip install -r requirements.txt

# Bundle app source
ADD . /home/user

# Install main module
RUN python setup.py install

# Expose
EXPOSE 5000

# Set user
USER user