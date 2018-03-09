[![Latest PyPI version](https://img.shields.io/pypi/v/ecstools.svg)](https://pypi.python.org/pypi/ecstools)
[![Build Status](https://travis-ci.org/boroivanov/ecs-tools.svg)](https://travis-ci.org/boroivanov/ecs-tools)

# ecstools
ECS Tools cli aims to make deploying to ECS Fargate easier. It also provides an easy way to scale
and update environment variables.

# Install
```bash
pip install ecstools
```
# Usage

## Listing
**List clusters**
```bash
$ ecs cluster ls
```
**List services**
```bash
$ ecs service ls <cluster>
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

The cli also auto-updates when doing a deployment. We get almost real-time information about all deployments for the service (there could be more that one). The output includes information for the number of containers in each deployment and their status. The number of containers in an ALB/NLB (if one is configured for the service) and their registration status. At the end we also get the last two events from the ECS service.

The cli will assume we are trying to deploy as many containers as there are in the current task definition for the service. If we pass the `-c` flag, we can scale in or out during the deployment.

Once the cli triggers the deploy and gets to the auto-update screen we can cancel the command if we want. The deployment is going to continue. We can always go back to monitor it with `ecs service top <cluster> <service>`

```bash
# Example of deploying a new docker tag
$ ecs service deploy cluster1 app1 tag-new-123
Current task deinition for cluster1 app1: app1-task-def:123
Found image: 123456789.dkr.ecr.us-east-1.amazonaws.com/app1:tag-new-123
Registerd new task definition: app1-task-def:124
Deploying app1-task-def:124 to cluster1 app1...

cluster1 app1                      app1-task-def:124  desired: 2 running: 2 pending: 2

Deployments:
    PRIMARY                     app1-task-def:124  desired: 2 running: 0 pending: 2
    ACTIVE                      app1-task-def:123  desired: 2 running: 2 pending: 0


Target Group: app1-tg  app1 443  healthy: 1 draining: 1

2018-03-07 17:37:34-08:00 (service app1) has started 2 tasks: (task 9ac2a0c9-4d9a-49eb-9928-3149fc975bd1) (task 51b3d856-d63e-4066-b871-2d36e9cc63f5).
2018-03-07 17:37:34-08:00 (service app1) has begun draining connections on 1 tasks.

# Example of deploying the same docker tag. A new deployment is forced to recycle containers.
$ ecs service deploy cluster1 app1 tag1
Current task deinition for cluster1 app1: app1-task-def:123
Found image: 123456789.dkr.ecr.us-east-1.amazonaws.com/app1:tag1
app1:tag1 is already in the current task definition. Forcing a new deployment of app1-task-def:123
Deploying app1-task-def:123 to cluster1 app1...

cluster1 app1                      app1-task-def:123  desired: 2 running: 2 pending: 2

Deployments:
    PRIMARY                     app1-task-def:123  desired: 2 running: 0 pending: 2
    ACTIVE                      app1-task-def:123  desired: 2 running: 2 pending: 0


Target Group: app1-tg  app1 443  healthy: 1 draining: 1

2018-03-07 17:37:34-08:00 (service app1) has started 2 tasks: (task 9ac2a0c9-4d9a-49eb-9928-3149fc975bd1) (task 51b3d856-d63e-4066-b871-2d36e9cc63f5).
2018-03-07 17:37:34-08:00 (service app1) has begun draining connections on 1 tasks.

# To scale during a deployment pass `-c N`
$ ecs service deploy cluster1 app1 tag1 -c 123
```

## Scaling
Scaling works by specifying cluster, service, and the number of desired containers. The cli auto-updates so we can see how many containers there are and what their ECS and ALB/NLB status is.

Once the cli triggers the scaling and gets to the auto-update screen we can cancel the command if we want. The scaling is going to continue. We can always go back to monitor it with `ecs service top <cluster> <service>`

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

Do you want to create a new task definition revision?

# Deleting environment variables
$ ecs service env cluster1 app1 TEST1=123 TEST2=456 -d
Current task definition for cluster1 app1: app1-task-def:123

Container: app1
- TEST1=123
- TEST2=456

Do you want to create a new task definition revision?
```

## Monitoring
We can either describe a service or "top" it. Both print information about the current task definition, the number of containers and their status in ECS and ALB/NLB. In addition, the describe command prints information about the subnets and security groups. On the other side, the top command auto-updates. The top command is useful if we want to monitor the progress of a deployment or a scaling event which we triggered by exited out of the deploy or scale commands.

```bash
# Describe a service
$ ecs service desc <cluster> <service>

# Live monitoring of a service
$ ecs service top <cluster> <service>
```

## AWS Profile and Region
We can use different AWS profile by specifying `-p <profile>` and different region with passing `-r <region>`.
