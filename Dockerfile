FROM python:3.10-bullseye
USER root

ENV POETRY_VERSION=1.4.1
# Clean up APT when done.
RUN apt update && \
    apt -y install \
        build-essential \
        zlib1g-dev \
        libssl-dev \
        libffi-dev \
        git \
        curl \
        wget \
        gcc \
        gfortran \
        libpq-dev \
        libbz2-dev \
        liblzma-dev \
        postgresql-client --no-install-recommends && \
    apt clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN pip3 install --upgrade pip
RUN pip3 install poetry==$POETRY_VERSION \
    && poetry config virtualenvs.create false

ARG NB_UID="1000"
ARG NB_GID="100"

ENV SAGERENDER_USER=sagerender

USER root
# Setup the "sagemaker" user with root privileges.
RUN \
    apt update && \
    apt install -y sudo && \
    useradd -m -s /bin/bash -N -u $NB_UID $SAGERENDER_USER && \
    chmod g+w /etc/passwd && \
    echo "${SAGERENDER_USER}    ALL=(ALL)    NOPASSWD:    ALL" >> /etc/sudoers && \
    # Prevent apt cache from being persisted to this layer.
    rm -rf /var/lib/apt/lists/*


ENV SAGERENDER_PROJECT=sagerender
ENV SAGERENDER_PROJECT_DIR=/opt/code

RUN mkdir -p $SAGERENDER_PROJECT_DIR/$SAGERENDER_PROJECT
COPY --chown=$SAGERENDER_USER:$NB_GID ./pyproject.toml ./poetry.lock ./README.md $SAGERENDER_PROJECT_DIR/$SAGERENDER_PROJECT
COPY --chown=$SAGERENDER_USER:$NB_GID ./sagerender $SAGERENDER_PROJECT_DIR/$SAGERENDER_PROJECT/sagerender
COPY --chown=$SAGERENDER_USER:$NB_GID ./tests $SAGERENDER_PROJECT_DIR/$SAGERENDER_PROJECT/tests
COPY --chown=$SAGERENDER_USER:$NB_GID ./examples $SAGERENDER_PROJECT_DIR/$SAGERENDER_PROJECT/examples
COPY --chown=$SAGERENDER_USER:$NB_GID ./extras $SAGERENDER_PROJECT_DIR/$SAGERENDER_PROJECT/extras
WORKDIR $SAGERENDER_PROJECT_DIR/$SAGERENDER_PROJECT/

RUN poetry install && poetry cache clear --all .

USER $SAGERENDER_USER

CMD ["sagerender"]
