import shlex
import subprocess
import sys

import click
from ecstools.commands.service.env import container_selection
from ecstools.resources.service import Service


@click.command(short_help='Run ECS Exec')
@click.argument('cluster')
@click.argument('service')
@click.argument('command', default='/bin/bash')
@click.option('-c', '--container', type=str, default=None, help='Container name')
@click.option('-t', '--task', type=str, default=None, help='Task id')
@click.pass_context
def exec(ctx, cluster, service, command, container, task):
    """Run ECS Exec"""
    ecs = ctx.obj['ecs']
    ecr = ctx.obj['ecr']

    try:
        if not task:
            tasks = ecs.list_tasks(cluster=cluster, serviceName=service, desiredStatus='RUNNING')
            task = tasks['taskArns'][0]
        task_desc = ecs.describe_tasks(cluster=cluster, tasks=[task])['tasks'][0]
    except Exception as e:
        sys.exit(e)

    task_id = task_desc['taskArn'].split('/')[-1]
    task_def = task_desc['taskDefinitionArn'].split('/')[-1]
    started_at = task_desc['startedAt'].replace(microsecond=0)
    click.echo(f'{task_id} {started_at} {task_def}')

    try:
        srv = Service(ecs, ecr, cluster, service)
        for c in srv.task_definition().containers():
            click.echo(f"\t{c['name']}: {c['image']}")
    except Exception as e:
        sys.exit(e)

    if not container:
        container_desc = container_selection(srv.task_definition().containers())
        container = container_desc['name']

    cmd = f'aws ecs execute-command --cluster {cluster} --task {task_id} --container {container}' \
        f' --command "{command}" --interactive'

    try:
        subprocess.check_call(shlex.split(cmd))
    except Exception as e:
        sys.exit(e)
