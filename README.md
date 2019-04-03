[![Latest PyPI version](https://img.shields.io/pypi/v/ecstools.svg)](https://pypi.python.org/pypi/ecstools)
[![Build Status](https://travis-ci.org/boroivanov/ecs-tools.svg)](https://travis-ci.org/boroivanov/ecs-tools)
[![Maintainability](https://api.codeclimate.com/v1/badges/2ac1865c995f49ee2eed/maintainability)](https://codeclimate.com/github/boroivanov/ecs-tools/maintainability)
[![Test Coverage](https://api.codeclimate.com/v1/badges/2ac1865c995f49ee2eed/test_coverage)](https://codeclimate.com/github/boroivanov/ecs-tools/test_coverage)
[![Downloads](https://pepy.tech/badge/ecstools)](https://pepy.tech/project/ecstools)
[![Downloads](https://pepy.tech/badge/ecstools/month)](https://pepy.tech/project/ecstools)

# ecstools
ECS Tools cli aims to make deploying to ECS Fargate easier. It also provides an easy way to scale
and update environment variables.

![Demo_gif](https://raw.githubusercontent.com/boroivanov/ecs-tools/master/images/ecs-tools-watcher.gif)

# Install
```bash
pip install ecstools
```
*NOTE: Python 2 is not supported as of version 0.1.7*

# Usage

## Config File
As of v0.1.6 the cli supports an INI config file. The cli will read config files from `~/.ecstools` and `$(pwd)/.ecstools`. The latter one will override settings from the former one. Hence, we can have config files per project and a global config to failback to. The config file can be used to set command aliases and/or service groups for multi-service deployments. An example config:
```ini
[alias]
cls = cluster ls
td = task-definition ls

ls = service ls
lsa = service ls -a
env = service env
deploy = service deploy
desc = service desc
scale = service scale
top = service top

# Example: Deploy service group to production cluster
dp = service deploy production app1 -g

[service-group]
app1 = app1 app1-worker1 app1-worker2
```


## Listing
**List clusters**
```bash
$ ecs cluster ls
```
**List services**
```bash
# List services in a cluster
$ ecs service ls <cluster>

# List service in a cluster with task definition info
$ ecs service ls <cluster> -a
```
**List task definition families**
```bash
$ ecs task-definition ls
```
**List task definition revisions with CPU, memory, and container information.**
```bash
# List the last 3 task definition revisions
$ ecs task-definition ls <task-definition-family>
app1-task-def:3 cpu: 1024 memory: 2048
  - container1 0 - container1:docker-tag3
  - container2 0 - container2:latest
app1-task-def:2 cpu: 1024 memory: 2048
  - container1 0 - creator:v1.2.3
  - container2 0 - container2:latest
app1-task-def:1 cpu: 1024 memory: 2048
  - container1 0 - container1:v0.0.1


# List more revisions
$ ecs task-definition ls <task-definition-family> -n 123
```


## Deploying
The deployments work by specifying cluster, service, and a docker tag.

The cli is going to check the current active task definition associated with the service and get the container name. Then it will create a new task definition revision with the new docker tag and deploy it. If the docker tag passed to the cli is the same as in the current task definition, a new deployment will be forced with the current task definition and containers will be recycled. This covers cases where we are deploying tag 'latest' but the tag was reassigned to a new image.

### Deploying - Service with multiple containers (Experimental)
As of v0.1.6 deploying a service with multiple containers is support in single-service deployment only. The cli doesn't yet support multi-service deployments with multiple containers.

To deploy multiple containers we need to pass the container tags in the same order the containers are defined in the task definition. If we have containers defined as [container1, container2] the deployment command will be:
```bash
ecs service deploy cluster1 app1 container1-tag container2-tag
```

### Deploying - Deploying Multiple Services
As of v0.1.6 the cli supports deploying multiple services at the same time. Once a service group has been configured in `~/.ecstools` we can trigger a group deployment by passing `-g`. See the [Config File](#config-file)

### Deploying - Auto-update Monitor
The cli output auto-updates during a deployment. We get almost real-time information about all deployments for the service (there could be more that one). The output includes information about:

- the name of the containers and their docker tags.
- the number of containers in each deployment and their status.
- the number of containers in an ALB/NLB (if one is configured for the service) and their registration status.
- the last two events from the ECS service.

### Deploying - Scaling during deployment
The cli will assume we are trying to deploy as many containers as there are in the current task definition for the service. If we pass the `-c` flag, we can scale in or out during the deployment.

### Deploying - Verbose Mode
We can turn verbose mode on with `-v` to get additional information before the deployment begins.

### Deploying - Post Deployment Monitoring
Once the cli triggers the deploy and gets to the auto-update screen we can cancel the command if we want with Ctrl-C. The deployment is going to continue. We can always go back to monitor it with `ecs service top <cluster> <service>`

### Deploying - Examples
```bash
# Example of deploying a single service
$ ecs service deploy cluster1 app1 tag-new-123
Elapsed: 00:00:04
InProgress  cluster1 app1          0/1  LB: [healthy: 1]

Ctrl-C to quit the watcher. No deployments will be interrupted.

# Example of deploying a service group
$ grep -B 1 app1 ~/.ecstools
[service-group]
octo = octo octo-worker1 octo-worker2

$ ecs service deploy octo octo:awscp-5513185 -g
...
```
![Demo_gif](https://raw.githubusercontent.com/boroivanov/ecs-tools/master/images/ecs-tools-watcher.gif)

Deploying and scaling at the same time.
```bash
# To scale during a deployment pass `-c N`
$ ecs service deploy cluster1 app1 tag1 -c 123
```

## Scaling
Scaling works by specifying cluster, service, and the number of desired containers. The cli auto-updates so we can see how many containers there are and what their ECS and ALB/NLB status is.

Once the cli triggers the scaling and gets to the auto-update screen we can cancel the command if we want with Ctrl-C. The scaling is going to continue. We can always go back to monitor it with `ecs service top <cluster> <service>`

```bash
$ ecs service scale <cluster> <service> 123
```

## Updating environment variables

Updating environment variables works by specifying cluster, service, and pairs of KEY=VALUE.

The cli will get the current task definition for the service and then compare its environment variables with the ones that were passed. The cli will print a git-style diff so we can review the changes. Then it will prompt if we want to register a new task definition and deploy it. Finally, the cli starts printing the default deployment auto-update output.

Once the cli triggers the deploy and gets to the auto-update screen we can cancel the command if we want. The deployment is going to continue. We can always go back to monitor it with `ecs service top <cluster> <service>`

```bash
# List environment variables
$ ecs service env <cluster> <service>

# Set/Update environment variables from a file
$ ecs service env cluster1 app1 "$(< file.txt)"

# Set/Update environment variables
$ ecs service env cluster1 app1 TEST1=123 TEST2=456
Current task definition for cluster1 app1: app1-task-def:123

Container: app1
+ TEST1=123
+ TEST2=456

Do you want to deploy your changes?

# Deleting environment variables
$ ecs service env cluster1 app1 TEST1=123 TEST2=456 -d
Current task definition for cluster1 app1: app1-task-def:123

Container: app1
- TEST1=123
- TEST2=456

Do you want to deploy your changes?
```
Updating environment variables for multiple service via service groups.
```bash
$ env stage app1 -g TEST=123456
Current task definition for stage app1: stage-app1:96
1) app1
2) nginx
#? 1

==> Container: app1
+ TEST=123456

Current task definition for stage app1-worker1: stage-app1-worker1:34

==> Container: app1
+ TEST=123456

Current task definition for stage app1-worker2: stage-app1-worker2:38

==> Container: app1
+ TEST=123456

Do you want to deploy your changes?
```

## Monitoring
We can either describe a service or "top" it. Both print information about the current task definition, the number of containers and their status in ECS and ALB/NLB. In addition, the describe command prints information about the subnets and security groups. On the other side, the top command auto-updates. The top command is useful if we want to monitor the progress of a deployment or a scaling event which we triggered by exited out of the deploy or scale commands.

```bash
# Describe a service
$ ecs service desc <cluster> <service>

# Live monitoring of a service
$ ecs service top <cluster> <service>

# Live monitoring of a service group
$ ecs service top <cluster> <service-group> -g
```

## AWS Profile and Region
We can use different AWS profile by specifying `-p <profile>` and different region with passing `-r <region>`.
