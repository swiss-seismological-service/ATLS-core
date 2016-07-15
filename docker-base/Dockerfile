FROM ubuntu:14.04
MAINTAINER Lukas Heiniger email: lukas.heiniger@sed.ethz.ch

ENV DEBIAN_FRONTEND noninteractive 

# Undo some leet hax of the base image that prevent services from starting on build
# (we need that, at least openquake expects it for things like rabbitmq)
RUN rm /usr/sbin/policy-rc.d

# Enables the commands below
RUN apt-get update && apt-get install -y software-properties-common wget

# Add OpenQuake Repository
RUN add-apt-repository ppa:openquake/release-1.9

# Add ObsPy sources
RUN echo "deb http://deb.obspy.org trusty main" >> /etc/apt/sources.list && \
    PUBLIC_KEY=https://raw.github.com/obspy/obspy/master/misc/debian/public.key && \
    wget --quiet -O - $PUBLIC_KEY | apt-key add -

# Install debian packages
RUN apt-get update && apt-get install -y --force-yes \
    dvipng=1.14-2 \
    git=1:1.9.1-1ubuntu0.3 \
    graphviz=2.36.0-0ubuntu3.1 \
    python-epydoc=3.0.1+dfsg-4 \
    python-lxml=3.3.3-1ubuntu0.1 \
    python-mock=1.0.1-3 \
    python-nose=1.3.1-2 \
    python-obspy=1.0.1-1~trusty \
    python-oq-engine \
    python-pip=1.5.4-1ubuntu3 \
    python-qt4=4.10.4+dfsg-1ubuntu1 \
    python-qt4-gl=4.10.4+dfsg-1ubuntu1 \
    python-sqlalchemy=0.8.4-1build1 \
    qgis=2.0.1-2build2 \
    texlive-latex-base=2013.20140215-1

# Install OpenQuake and update db 
RUN service postgresql start && oq-engine --upgrade-db -y

# Install PIP packages
RUN pip install \
    flask==0.11.1 \
    flask-restless==0.17.0 \
    flask-sqlalchemy==2.1 \
    numpy==1.8.2 \
    pymatlab==0.2.3 \
    sphinx==1.4.1 \
    sphinx-rtd-theme==0.1.9

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
