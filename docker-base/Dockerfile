FROM ubuntu:14.04
MAINTAINER Lukas Heiniger email: lukas.heiniger@sed.ethz.ch

ENV DEBIAN_FRONTEND noninteractive 

# Undo some leet hax of the base image that prevent services from starting on build
# (we need that, at least openquake expects it for things like rabbitmq)
RUN rm /usr/sbin/policy-rc.d

# Enables the commands below
RUN apt-get install -y software-properties-common wget

# Add OpenQuake Repository
RUN add-apt-repository ppa:openquake/ppa

# Add ObsPy sources
RUN echo "deb http://deb.obspy.org trusty main" >> /etc/apt/sources.list && \
    PUBLIC_KEY=https://raw.github.com/obspy/obspy/master/misc/debian/public.key && \
    wget --quiet -O - $PUBLIC_KEY | apt-key add -

# Install debian packages
RUN apt-get update && apt-get install -y --force-yes \
	graphviz \
	git \
	python-lxml \
	python-mock \
	python-nose \
	python-obspy \
	python-pip \
	python-qt4 \ 
	python-qt4-gl \
	python-sqlalchemy \
	qgis

# Install OpenQuake and update db 
RUN apt-get install -y python-oq-engine && \
	oq-engine --upgrade-db -y

# Install PIP packages
RUN pip install \
	numpy \
	pymatlab \
	sphinx \
	sphinx-rtd-theme

# Install custom pyqtgraph version
RUN git clone https://github.com/3rdcycle/pyqtgraph.git /tmp/pyqtgraph && \
	cd /tmp/pyqtgraph && \
	git checkout date-axis-item && \
	python setup.py install && \
	cd - && rm -rf /tmp/pyqtgraph

# Install custom GSIMs
COPY oq-gmpe-gsim/* /usr/lib/python2.7/dist-packages/openquake/hazardlib/gsim/

# Set QGIS prefix path
ENV QGIS_PREFIX_PATH /usr
