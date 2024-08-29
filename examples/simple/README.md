## SageRender Configuration with different environments
The `hiera.yaml` file is a configuration file for [Phiera](https://github.com/nike-inc/phiera), a key-value lookup tool
for configuration data. It is used to separate data from code. In this project, it is used to manage the configuration
data of different environments for SageMaker Pipelines.

The `hiera.yaml` file has the following structure:

```yaml
---
backends:
  - yaml

# Define context, context variables can be arbitrary.
# In this example, let's use familiar ones such as:
# env: Name of the environment, which can be prod, dev, qa
context:
  - env

# The order of precedence is from least to most.
hierarchy:
  - common
  - "environment/%{env}"

yaml:
  # datadir folder
  datadir: examples/simple
```

The `backends` field specifies the backend data sources Phiera should use. In this case, it's using YAML files.

The `context` field specifies the context variables that Phiera uses to determine which data to fetch. In this case,
it's using `env`.

The `hierarchy` field specifies the hierarchy of data sources. Phiera will look for data in these sources in the order
they are listed. In this case, it first looks in the `common` data source, then in the `environment/%{env}` data
source (where `%{env}` is replaced with the value of the `env` context variable). In this example in the hierarchy, the
`environment` section has the highest precedence followed by `common`.

The `yaml` field specifies the configuration for the YAML backend. In this case, it's specifying that the data
directory (where the YAML files are located) is `examples/simple`.

The referenced files in the `examples/simple` directory provide the actual data for the different data sources.
For example, the `common.yaml` file provides data for the `common` data source, the `environment/dev.yaml` file
provides data for the `environment/dev` data source, and so on. These files are written in YAML and contain key-value
pairs of configuration data.

The `common.yaml` file contains the common configurations for all the pipelines. It includes the session bucket,
S3 bucket prefix, tags, and the standard model training pipeline configuration.

The `environment/*.yaml` files contain environment-specific configurations. For example, the `dev.yaml` file contains
the resource configuration and bucket prefix for the `dev` environment.

By using Phiera, you can manage the configuration data of different environments in a structured and organized way.
This makes it easier to maintain and update the configuration data as your project evolves.
