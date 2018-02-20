# ecs-tools


# Install
```bash
pip install ecs-tools
```
# Usage
List clusters and/or their services
```bash
ecs ls
ecs ls <cluster>
```
List / Describe task definitions
```bash
# List task definition families
ecs def
# List task definition revisions
ecs def <task-definition-family>
# List a specific task definition revision
ecs def <task-definition-family>:<revision>
```
Scale services
```bash
ecs scale <cluster> <service> 123
```

#### Deploy Task Def
ecs service deploy cls-name srv-name --task-definition task-name # deploys latest task def
ecs service deploy cls-name srv-name --task-definition task-name:rev123
#### Deploy ECR Images
ecs service deploy cls-name srv-name --ecr-image IMAGE  # deploys latest
ecs service deploy cls-name srv-name --ecr-image IMAGE:TAG123
#### Deploy DVCS refs
ecs service deploy cls-name srv-name --dvcs <githib|bitbucket|CodeCommit> --org GH-ORG --repo REPO --ref BRANCH # dcvs default: github
ecs service deploy cls-name srv-name --dvcs <githib|bitbucket|CodeCommit> --org GH-ORG --repo REPO --ref TAG
ecs service deploy cls-name srv-name --dvcs <githib|bitbucket|CodeCommit> --org GH-ORG --repo REPO --ref SHA

**ecs deploy staging coop master** # Asks for config if none found

ecs deploy creator-cls 879a8sdf           # create tasks def for all services and deploy
ecs deploy creator-cls worker1 879a8sdf
ecs deploy creator-cls worker1 worker2 879a8sdf
ecs deploy creator-cls --task-definition creator-stage-def:123
ecs deploy creator-cls worker1 --taks-definition creator-stage-def:123
ecs notifications
ecs notifications creator-cls
ecs notifications add creator-cls --all
ecs notifications add creator-cls --scaling-event
ecs notifications add creator-cls --deploy-started
ecs notifications add creator-cls --deploy-failed
ecs notifications add creator-cls --deploy-succeeded
