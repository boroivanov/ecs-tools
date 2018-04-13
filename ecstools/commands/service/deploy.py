import click
import sys

from botocore.exceptions import ClientError

import ecstools.lib.utils as utils


@click.command(short_help='Deploy service')
@click.argument('cluster')
@click.argument('service')
@click.argument('artifact')
@click.option('-T', '--task-definition', is_flag=True, help='Deploy task definition')
@click.option('-c', '--count', type=int, default=None, help='Update the current number of tasks')
@click.pass_context
def cli(ctx, cluster, service, artifact, task_definition, count):
    """Deploy a task definition to a service

    |\b
    The deployment respects the current number of tasks in the service.
    Use '-c' to scale in or out during deploy.
    """
    ecs = ctx.obj['ecs']
    ecr = ctx.obj['ecr']
    elbv2 = ctx.obj['elbv2']

    task_def = artifact
    if not task_definition:
        task_def = register_task_def_with_new_image(
            ecs, ecr, cluster, service, artifact)

    deploy_task_definition(ecs, cluster, service, task_def, count)

    click.echo()
    utils.monitor_deployment(ecs, elbv2, cluster, service)


def register_task_def_with_new_image(ecs, ecr, cluster, service, artifact):
    # Get ECR repo
    srv = desc_service(ecs, cluster, service)
    td_arn = srv['taskDefinition']
    click.echo('Current task deinition for %s %s: %s' %
               (cluster, service, td_arn.split('/')[-1]))
    td = desc_task_definition(ecs, td_arn)
    containers = td['containerDefinitions']

    try:
        ecr_repo, ecr_iamge_tag = containers[0]['image'].split(':')
    except:
        # If no tag was specified - defaulting to latest tag
        ecr_repo = containers[0]['image']

    # Check if image tag exist in the ECR repo
    try:
        ecr.describe_images(
            repositoryName=ecr_repo.split('/')[-1],
            imageIds=[
                {
                    'imageTag': artifact
                },
            ],
            filter={
                'tagStatus': 'TAGGED'
            }
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'ImageNotFoundException':
            click.echo('Image not found: %s' % e, err=True)
        else:
            click.echo(e, err=True)
        sys.exit(1)

    click.echo('Found image: %s:%s' % (ecr_repo, artifact))

    ###########################################################################
    # Force new deployment with the current active task definition if
    # the requested for docker image tag is the same.
    # We need to recycle containers in case the tag was reassigned to different
    # docker image (think tag:latest).
    # We skip registering a new task definition revision as it's not needed.
    ###########################################################################
    if ecr_iamge_tag and ecr_iamge_tag == artifact:
        click.secho(('%s:%s is already in the current task definition. ' % (
            ecr_repo.split('/')[-1], ecr_iamge_tag)), nl=False, fg='white')
        click.secho(('Forcing a new deployment of %s' %
                     td_arn.split('/')[-1]), fg='white')
        return td_arn

    ###########################################################################
    # Register new task definition with the new image
    ###########################################################################
    new_td = td.copy()
    for k in ['status', 'compatibilities', 'taskDefinitionArn', 'revision', 'requiresAttributes']:
        del new_td[k]
    new_td['containerDefinitions'][0]['image'] = ':'.join([ecr_repo, artifact])
    new_td_res = ecs.register_task_definition(**new_td)
    td_name = new_td_res['taskDefinition']['taskDefinitionArn'].split('/')[-1]
    click.secho('Registered new task definition: %s' % td_name, fg='green')

    return td_name


def deploy_task_definition(ecs, cluster, service, task_def, count):
    click.secho('Deploying %s to %s %s...' %
                (task_def.split('/')[-1], cluster, service), fg='blue')
    params = {
        'cluster': cluster,
        'service': service,
        'taskDefinition': task_def,
        'forceNewDeployment': True
    }

    if count:
        params['desiredCount'] = count

    res = ecs.update_service(**params)
    return res


def desc_service(ecs, cluster, service):
    try:
        res = ecs.describe_services(
            cluster=cluster,
            services=[service]
        )
        srv = res['services'][0]
    except ClientError as e:
        if e.response['Error']['Code'] == 'ClusterNotFoundException':
            click.echo('Cluster not found.', err=True)
        else:
            click.echo(e, err=True)
        sys.exit(1)
    except:
        click.echo('Service not found.', err=True)
        sys.exit(1)

    return srv


def desc_task_definition(ecs, taskDefinition):
    res = ecs.describe_task_definition(taskDefinition=taskDefinition)
    return res['taskDefinition']
