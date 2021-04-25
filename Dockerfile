# Use an official Python runtime as a parent image
FROM python:3.9.4-buster
RUN apt-get update && apt-get install -y \
    gosu gettext \
 && rm -rf /var/lib/apt/lists/*

# Set the working directory to /opt/application
WORKDIR /opt/application

# create application user
RUN useradd --create-home application

RUN chown -R application /opt/application
RUN mkdir /opt/rundir
RUN chown -R application /opt/rundir
RUN mkdir /opt/venv
RUN chown -R application /opt/venv
# Copy the current directory contents into the container at /opt/application
COPY backend/requirements.txt /tmp/requirements.txt
COPY backend/requirements-dev.txt /tmp/requirements-dev.txt

# change to non-root user
USER application

RUN python -m venv /opt/venv
# Install any needed packages specified in requirements.txt
RUN /opt/venv/bin/pip install --upgrade pip==21.0.1 setuptools
RUN /opt/venv/bin/pip install --disable-pip-version-check --trusted-host pypi.python.org -r /tmp/requirements.txt --no-cache-dir
RUN /opt/venv/bin/pip install --disable-pip-version-check --trusted-host pypi.python.org -r /tmp/requirements-dev.txt --no-cache-dir
# make application scripts visible
ENV PATH /opt/venv/bin:$PATH
ENV APP_ENV development
ENV APP_INI_FILE development.ini
ENV TESTING_INI testing.ini
# expose build tag to application
ARG TAG
ENV TAG=$TAG
USER root
USER application
WORKDIR /opt/application
COPY --chown=application .git /tmp/.git
# Copy the current directory contents into the container at /opt/application
COPY --chown=application backend /opt/application
# save application revision
USER root
RUN cd /tmp/.git; git rev-parse HEAD > /opt/APPLICATION_COMMIT.txt
RUN cd /tmp/.git; echo testsaffold:`git rev-parse HEAD` > /opt/BUILD_TAG.txt
LABEL "com.app.service"="Test App"
RUN rm -rf /tmp/.git
USER application
# install the app
# https://thekev.in/blog/2016-11-18-python-in-docker/index.html
# https://jbhannah.net/articles/python-docker-disappearing-egg-info
ENV PYTHONPATH=/opt/application
RUN cd /opt/venv/; /opt/venv/bin/python /opt/application/setup.py develop
EXPOSE 6543
USER root
VOLUME /opt/application
VOLUME /opt/rundir
COPY docker/docker-entrypoint.sh /opt/docker-entrypoint.sh
COPY docker/entrypoint.d /opt/entrypoint.d
WORKDIR /opt/rundir
ENTRYPOINT ["/opt/docker-entrypoint.sh"]
# Run application when the container launches
CMD ["pserve", "/opt/rundir/config.ini"]
