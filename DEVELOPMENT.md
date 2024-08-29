# Local Development Setup for SageRender

This guide will walk you through setting up a local development environment
for the SageRender project using either Poetry or Docker Compose.

## Using Poetry

Poetry is a tool for dependency management and packaging in Python. It allows 
you to declare the libraries your project depends on, and it will 
manage (install/update) them for you.

### Prerequisites

- Python 3.10 or higher
- Poetry (Install it using the following command)

```shell
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python
```

### Steps

1. Clone the SageRender repository to your local machine.

```shell
git clone https://github.com/nike-inc/sagerender.git
```

2. Navigate to the project directory.

```shell
cd sagerender
```

3. Install the project dependencies.

```shell
poetry install
```

4. Run the unit tests to verify everything is set up correctly.

```shell
poetry run pytest
```

5. You can also run pre-commit checks using the following command.

```shell
poetry run pre-commit run --all-files
```

## Using Docker Compose

[Docker Compose](https://docs.docker.com/compose/) is a tool for 
defining and running multi-container Docker applications. 
With Docker Compose, you use a YAML file to configure your 
application's services.

### Prerequisites

- Docker
- Docker Compose

### Steps

1. Clone the SageRender repository to your local machine.

```shell
git clone https://github.com/nike-inc/sagerender.git
```

2. Navigate to the project directory.

```shell
cd sagerender
```

3. Build and run the Docker container.

```shell
docker compose -f docker-compose.yaml run --rm sagerender
```

This command will build the Docker image if the image does not exist,
and run a container named `sagerender`. The container will mount the 
current directory and your AWS credentials, and set the working 
directory to the current directory. At the end of the execution, you 
will land inside the docker container.

You can verify the docker container by running pytest using the 
following command:
```shell
pytest
```

Remember to replace `sagerender` with the actual name of your 
running Docker container if you decide the change the service name.

That's it! You now have a local development environment for the 
SageRender project set up using either Poetry or Docker Compose.
