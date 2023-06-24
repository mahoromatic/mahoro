ARG PYTHON_IMAGE_TAG="3.10-slim"
FROM python:${PYTHON_IMAGE_TAG}

ARG APP_HOME=/opt/mahoro
ARG DATA_DIR=/data

COPY . ${APP_HOME}

RUN apt-get update -yqq \
    && apt-get upgrade -yqq \
    && pip install -q --no-cache-dir --upgrade pip \
    && pip install -q --no-cache-dir -r ${APP_HOME}/requirements.txt \
    && useradd -ms /bin/bash -d ${APP_HOME} mahoro \
    && mkdir -p ${DATA_DIR} \
    && chown -R mahoro ${DATA_DIR}

USER mahoro

WORKDIR ${APP_HOME}

ENTRYPOINT [ "python", "src/plus.py" ]
ENV PLUS_CONFIG=${APP_HOME}/config.ini
