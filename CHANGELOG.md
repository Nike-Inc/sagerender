# Changelog

All notable changes to this project will be documented in this file.<br/>
`sagerender` adheres to [Semantic Versioning](http://semver.org/).

#### 2.x Releases
- `2.1.x` Releases - [2.1.0](#210) | [2.1.1](#211) | [2.1.2](#212) | [2.1.3](#213)
- `2.0.x` Releases - [2.0.0](#200)

#### 1.x Releases
- `1.6.x` Releases - [1.6.0](#160)
- `1.5.x` Releases - [1.5.0](#150) | [1.5.1](#151) | [1.5.2](#152)
- `1.4.x` Releases - [1.4.0](#140)
- `1.3.x` Releases - [1.3.0](#130)
- `1.2.x` Releases - [1.2.0](#120) | [1.2.1](#121) | [1.2.2](#122) | [1.2.3](#123)
- `1.1.x` Releases - [1.1.0](#110)
- `1.0.x` Releases - [1.0.0](#100)
- `1.0.0-alpha` Releases - [1.0.0-alpha0](#100-alpha0) | [1.0.0-alpha1](#100-alpha1) | [1.0.0-alpha2](#100-alpha2) | [1.0.0-alpha3](#100-alpha3)

---
## Unreleased

#### Added

#### Updated

#### Deprecated

#### Removed

#### Fixed

---
## 2.1.3
#### Added
* Added License information in pyproject.toml

---
## 2.1.2
#### Fixed
* Fixed Github organization

---
## 2.1.1
#### Updated
* Updated third party dependencies.

---
## 2.1.0
#### Updated
* Updated `cerberus` configuration to make host as required
  * Added by [Mohamed Abdul Huq Ismail](https://github.com/aisma7_nike) in Pull Request [#31](https://github.com/Nike-Inc/sagerender/pull/31) 

---
## 2.0.0
#### Added
* Add support for configuring [Pipeline Experiments](https://sagemaker.readthedocs.io/en/stable/workflows/pipelines/sagemaker.workflow.pipelines.html#pipeline-experiment-config)
  * Added by [Mohamed Abdul Huq Ismail](https://github.com/aisma7_nike) in Pull Request [#30](https://github.com/Nike-Inc/sagerender/pull/30)
* Add support for configuring [Pipeline Definition](https://sagemaker.readthedocs.io/en/stable/workflows/pipelines/sagemaker.workflow.pipelines.html#pipeline-definition-config)
  * Added by [Mohamed Abdul Huq Ismail](https://github.com/aisma7_nike) in Pull Request [#30](https://github.com/Nike-Inc/sagerender/pull/30)
* Add support for resolving generic enums by defining `factory_enum`
  * Added by [Mohamed Abdul Huq Ismail](https://github.com/aisma7_nike) in Pull Request [#30](https://github.com/Nike-Inc/sagerender/pull/30)
* Add support for all missing [SageMaker Pipeline Step Types](https://docs.aws.amazon.com/sagemaker/latest/dg/build-and-manage-steps.html#build-and-manage-steps-types)
  * Added by [Mohamed Abdul Huq Ismail](https://github.com/aisma7_nike) in Pull Request [#30](https://github.com/Nike-Inc/sagerender/pull/30)
* Add support for resolving environment variables defined in YAML using ${ENV_VAR} syntax
  * Added by [Mohamed Abdul Huq Ismail](https://github.com/aisma7_nike) in Pull Request [#30](https://github.com/Nike-Inc/sagerender/pull/30)
* Add support for providing resource configuration as part of the YAML configuration as an alternative.
  * Added by [Mohamed Abdul Huq Ismail](https://github.com/aisma7_nike) in Pull Request [#30](https://github.com/Nike-Inc/sagerender/pull/30)

#### Updated
* Updated `PipelineBuilder` class to use `StepModel` to instantiate the appropriate step based on the configuration keys
  * Updated by [Mohamed Abdul Huq Ismail](https://github.com/aisma7_nike) in Pull Request [#30](https://github.com/Nike-Inc/sagerender/pull/30)
* Updated yaml to load using ruamel.yaml instead of PyYaml as ruamel.yaml supports YAML 1.2 specification.
  * Updated by [Mohamed Abdul Huq Ismail](https://github.com/aisma7_nike) in Pull Request [#30](https://github.com/Nike-Inc/sagerender/pull/30)

#### Removed
* Removed `StepBuilder` class in favor of `StepModel` that uses pydantic to validate and instantiate the correct SageMaker Pipeline Step
  * Removed by [Mohamed Abdul Huq Ismail](https://github.com/aisma7_nike) in Pull Request [#30](https://github.com/Nike-Inc/sagerender/pull/30)
* Removed support for `inputs` and `outputs` base dictionaries for Processing Steps in favor of factory functions
  * Removed by [Mohamed Abdul Huq Ismail](https://github.com/aisma7_nike) in Pull Request [#30](https://github.com/Nike-Inc/sagerender/pull/30)

---
## 1.6.0
#### Added
* Add support for [ParallelismConfiguration](https://sagemaker.readthedocs.io/en/stable/workflows/pipelines/sagemaker.workflow.pipelines.html#parallelism-configuration)
  * Added by [Mohamed Abdul Huq Ismail](https://github.com/aisma7_nike) in Pull Request [#28](https://github.com/Nike-Inc/sagerender/pull/28)
* Add support for [SageMaker Pipeline Variables](https://sagemaker.readthedocs.io/en/stable/workflows/pipelines/sagemaker.workflow.pipelines.html#sagemaker.workflow.entities.PipelineVariable)
which includes SageMaker Primitive Types and Functions.
  * Added by [Mohamed Abdul Huq Ismail](https://github.com/aisma7_nike) in Pull Request [#28](https://github.com/Nike-Inc/sagerender/pull/28)
* Add support for [SageMaker Properties](https://sagemaker.readthedocs.io/en/stable/workflows/pipelines/sagemaker.workflow.pipelines.html#properties)
  * Added by [Mohamed Abdul Huq Ismail](https://github.com/aisma7_nike) in Pull Request [#28](https://github.com/Nike-Inc/sagerender/pull/28)

#### Updated
* Update third-party dependencies to latest available stable versions.
  * Updated by [Mohamed Abdul Huq Ismail](https://github.com/aisma7_nike) in Pull Request [#28](https://github.com/Nike-Inc/sagerender/pull/28)
* Update pre-commit hooks to latest available stable versions.
  * Updated by [Mohamed Abdul Huq Ismail](https://github.com/aisma7_nike) in Pull Request [#28](https://github.com/Nike-Inc/sagerender/pull/28)

---
## 1.5.2
#### Fixed
* Fixed logging to set up log handler and formatter in a secure way.
  * Fixed by [Mohamed Abdul Huq Ismail](https://github.com/aisma7_nike) in Pull Request [#29](https://github.com/Nike-Inc/sagerender/pull/29)
* Fixed Docker image and addressed security concerns reported by Sonar Scan.
  * Fixed by [Mohamed Abdul Huq Ismail](https://github.com/aisma7_nike) in Pull Request [#29](https://github.com/Nike-Inc/sagerender/pull/29)

---
## 1.5.1
#### Added
* Added module level annotations
    * Added by [Divyanshu Narendra](https://github.com/dnare1_nike) in Pull Request [#26](https://github.com/Nike-Inc/sagerender/pull/26/files)

---
## 1.5.0
#### Added
* Add `session_bucket` key to pipeline YAML definition to configure pipeline session bucket
    * Added by [Mohamed Abdul Huq Ismail](https://github.com/aisma7_nike) in Pull Request [#25](https://github.com/Nike-Inc/sagerender/pull/25)

---
## 1.4.0
#### Added
* Add support for [Retry Policies](https://docs.aws.amazon.com/sagemaker/latest/dg/pipelines-retry-policy.html) to Sagerender
  * Added by [Hari Ramachandran](https://github.com/hrama1_nike) in Pull Request [#21](https://github.com/Nike-Inc/sagerender/pull/21)

---
## 1.3.0
#### Added
* Add [CacheConfig](https://docs.aws.amazon.com/sagemaker/latest/dg/pipelines-caching.html) possibility to Sagerender
  * Added by [Saniya Lakka](https://github.com/slakka_nike) in Pull Request [#17](https://github.com/Nike-Inc/sagerender/pull/17)

---
## 1.2.3
#### Updated
* enable passing --debug to run_pipeline in order to have logs for the pipeline return to local environment.
   * Added by [Matthew Baron](https://github.com/mbaro6_nike) in Pull Request [#18](https://github.com/Nike-Inc/sagerender/pull/18)

---
## 1.2.2
#### Updated
* Update sagemaker version to > 2.159.0 and PyYaml version to >6.0.0. This is to enable `default_bucket_prefix` for sagemaker Pipeline which is available from 2.158.0
* Add optional arg to upsert_pipeline cli to support `default_bucket_prefix`
  * Added by [Rose Jones](https://github.com/rjon81_nike) in Pull Request [#15](https://github.com/Nike-Inc/sagerender/pull/14)

---
## 1.2.1
#### Fixed
* Some step kwargs parameters were not being replaced with sagemaker parameters.
  * Added by [Matt Struble](https://github.com/mstru3_nike) in Pull Request [#14](https://github.com/Nike-Inc/sagerender/pull/14)

---
## 1.2.0
#### Added
* Added support for parameter substitution for any of the step arguments.
  * Added by [Matt Struble](https://github.com/mstru3_nike) in Pull Request [#13](https://github.com/Nike-Inc/sagerender/pull/13)

---
## 1.1.0
#### Added
* Added support for Python3.10
  * Added by [Sławomir Strehlau](https://github.com/sstreh_nike) in Pull Request [#11](https://github.com/Nike-Inc/sagerender/pull/10)

---
## 1.0.0
#### Added
* Added support for all processors in processing step type.
  * Added by [Mohamed Abdul Huq Ismail](https://github.com/aisma7_nike) in Pull Request [#11](https://github.com/Nike-Inc/sagerender/pull/11)

#### Updated
* Updated upsert-pipeline CLI to use `PipelineSession` as recommended by AWS
  * Updated by [Mohamed Abdul Huq Ismail](https://github.com/aisma7_nike) in Pull Request [#11](https://github.com/Nike-Inc/sagerender/pull/11)
* `processor.get_run_args` is updated to `processor.run` due to future deprecation of the former by sagemaker python-sdk.
  * Updated by [Mohamed Abdul Huq Ismail](https://github.com/aisma7_nike) in Pull Request [#11](https://github.com/Nike-Inc/sagerender/pull/11)
* `job_arguments` in *step_kwargs* needs to be refactored to `arguments`.
  * Updated by [Mohamed Abdul Huq Ismail](https://github.com/aisma7_nike) in Pull Request [#11](https://github.com/Nike-Inc/sagerender/pull/11)

---
## 1.0.0-alpha3
#### Fixed
* Fixed script path for SageRender CLI.
  * Fixed by [Tanushri Sundar](https://github.com/tsund1_nike) in Pull Request [#9](https://github.com/Nike-Inc/sagerender/pull/9)

---
## 1.0.0-alpha2
#### Added
* Added `PipelineBuilder` to build SageMaker pipeline.
  * Added by [Mohamed Abdul Huq Ismail](https://github.com/aisma7_nike) in Pull Request [#8](https://github.com/Nike-Inc/sagerender/pull/8)
* Added `StepBuilder` to build SageMaker pipeline.
  * Added by [Mohamed Abdul Huq Ismail](https://github.com/aisma7_nike) in Pull Request [#8](https://github.com/Nike-Inc/sagerender/pull/8)
* Added simple documentation to use SageRender.
  * Added by [Mohamed Abdul Huq Ismail](https://github.com/aisma7_nike) in Pull Request [#8](https://github.com/Nike-Inc/sagerender/pull/8)
* Added support for running pipeline in local mode.
  * Added by [Mohamed Abdul Huq Ismail](https://github.com/aisma7_nike) in Pull Request [#8](https://github.com/Nike-Inc/sagerender/pull/8)

#### Updated
* Updated CLI to use SageRender interface.
  * Updated by [Mohamed Abdul Huq Ismail](https://github.com/aisma7_nike) in Pull Request [#8](https://github.com/Nike-Inc/sagerender/pull/8)
* Refactored code to use classes and objects.
  * Updated by [Mohamed Abdul Huq Ismail](https://github.com/aisma7_nike) in Pull Request [#8](https://github.com/Nike-Inc/sagerender/pull/8)
* Refactored `step_args` to `step_kwargs` for defining processing step kwargs.
  * Updated by [Mohamed Abdul Huq Ismail](https://github.com/aisma7_nike) in Pull Request [#8](https://github.com/Nike-Inc/sagerender/pull/8)

---
## 1.0.0-alpha1
#### Added
* Added support to configure sagemaker pipeline name.
  * Added by [Mohamed Abdul Huq Ismail](https://github.com/aisma7_nike) in Pull Request [#6](https://github.com/Nike-Inc/sagerender/pull/6)

---
## 1.0.0-alpha0
#### Added
* Added Cerberus integration to retrieve team specific resource and network configurations.
  * Added by [Mohamed Abdul Huq Ismail](https://github.com/aisma7_nike) in Pull Request [#5](https://github.com/Nike-Inc/sagerender/pull/5)
* Added support for upsert-pipeline cli.
  * Added by [Mohamed Abdul Huq Ismail](https://github.com/aisma7_nike) in Pull Request [#5](https://github.com/Nike-Inc/sagerender/pull/5)
* Added `PipelineBlueprint` to deal with hierarchical configurations.
  * * Added by [Mohamed Abdul Huq Ismail](https://github.com/aisma7_nike) in Pull Request [#5](https://github.com/Nike-Inc/sagerender/pull/5)

#### Updated
* Renamed sagemakerparser to sagerender.
  * Updated by [Mohamed Abdul Huq Ismail](https://github.com/aisma7_nike) in Pull Request [#5](https://github.com/Nike-Inc/sagerender/pull/5)
* Updated run-pipeline cli.
  * Updated by [Mohamed Abdul Huq Ismail](https://github.com/aisma7_nike) in Pull Request [#5](https://github.com/Nike-Inc/sagerender/pull/5)

#### Removed
* Removed legacy files and examples.
  * Removed by [Mohamed Abdul Huq Ismail](https://github.com/aisma7_nike) in Pull Request [#5](https://github.com/Nike-Inc/sagerender/pull/5)

---
