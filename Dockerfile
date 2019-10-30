FROM ubuntu:18.04

# Create limited user for Celery
RUN groupadd user && useradd --create-home --home-dir /home/user -g user user

# Set WORKDIR to /home/user
WORKDIR /home/user

# Update packages and install pip
RUN DEBIAN_FRONTEND=noninteractive apt-get update -y && apt-get -y install python3 python3-pip python3-dev libpq-dev libffi-dev

# Add and install Python modules
ADD requirements.txt /home/user/requirements.txt
RUN pip3 install -r requirements.txt

# Bundle app source
ADD . /home/user

# Install main module
RUN python3 setup.py install

# Expose
EXPOSE 5000

# Set user
USER user
