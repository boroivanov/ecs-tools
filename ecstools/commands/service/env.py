import click
import sys

import ecstools.lib.utils as utils


@click.command(short_help='Manage environment variables')
@click.argument('cluster', nargs=1)
@click.argument('service', nargs=1)
@click.argument('pairs', nargs=-1)
# @click.option('-c', '--container', help='Optional container name')
@click.pass_context
def cli(ctx, cluster, service, pairs):
    """Manage environment variables

    |\b
    # List environment variables
    $ ecs service env CLUSTER SERVICE

    # Set environment variables
    $ ecs service env CLUSTER SERVICE KEY1=VALUE1 KEY2=VALUE2 ...
    """
    ecs = ctx.obj['ecs']
    elbv2 = ctx.obj['elbv2']

    srv = desc_service(ecs, cluster, service)
    td_arn = srv['taskDefinition']
    click.secho('Current task deinition for %s %s: %s' %
                (cluster, service, td_arn.split('/')[-1]), fg='blue')
    td = desc_task_definition(ecs, td_arn)
    containers = td['containerDefinitions']

    if len(containers) > 1:
        container = container_selection(containers)
    else:
        container = containers[0]

    click.echo()

    click.secho(('Container: %s' % container['name']), fg='white')

    # Just print env vars if none were passed
    if len(pairs) == 0:
        for e in container['environment']:
            click.echo('%s=%s' % (e['name'], e['value']))
        sys.exit(0)

    validate_pairs(pairs)

    envs = container['environment'][:]

    # Update env var if it exist. Otherwise append it.
    for pair in pairs:
        k, v = pair.split('=', 1)
        matched = False
        # Check if env var already exists
        for e in envs:
            if k == e['name']:
                if v != e['value']:
                    # Env var value is different
                    click.echo('- %s=%s' % (e['name'], e['value']))
                    click.echo('+ ', nl=False)
                    e['value'] = v
                click.echo('%s=%s' % (k, v))
                matched = True
                break
        if not matched:
            click.echo('+ %s=%s' % (k, v))
            envs.append({'name': k, 'value': v})

    click.echo()
    try:
        c = input('Do you want to create a new task definition revision? ')
        if c not in ['yes', 'Yes', 'y', 'Y']:
            raise
    except:
        sys.exit(0)

    # Register new task definition with the new environment variables
    td_name = register_task_definition_with_envs(
        ecs, td, container['name'], envs)

    # # Ask to deploy the changes
    try:
        to_deploy = input('Do you want to deploy your changes? ')
        if to_deploy not in ['yes', 'Yes', 'y', 'Y']:
            raise
    except:
        sys.exit(0)

    # Deploy the new task definition
    deploy_task_definition(ecs, cluster, service, td_name)
    click.echo()
    utils.monitor_deployment(ecs, elbv2, cluster, service)


def register_task_definition_with_envs(ecs, current_task_definition, container, envs):
    """ Register new task definition with the new environment variables """
    new_td = current_task_definition.copy()
    for k in ['status', 'compatibilities', 'taskDefinitionArn', 'revision', 'requiresAttributes']:
        del new_td[k]
    for c in new_td['containerDefinitions']:
        if c['name'] == container:
            c['environment'] = envs
            new_td_res = ecs.register_task_definition(**new_td)
            td_name = new_td_res['taskDefinition']['taskDefinitionArn'].split(
                '/')[-1]
            click.secho('Registerd new task definition: %s' %
                        td_name, fg='green')

    return td_name


def deploy_task_definition(ecs, cluster, service, task_def):
    click.secho('Deploing %s to %s %s...' %
                (task_def, cluster, service), fg='blue')
    params = {
        'cluster': cluster,
        'service': service,
        'taskDefinition': task_def,
        'forceNewDeployment': True
    }
    res = ecs.update_service(**params)
    return res


def validate_pairs(pairs):
    for pair in pairs:
        if len(pair.split('=', 1)) != 2:
            click.echo('Not a valid pair: %s' % pair)
            sys.exit(1)


def container_selection(containers):
    for c in containers:
        click.echo('%s) %s' % (containers.index(c) + 1, c['name']))

    try:
        c = int(input('#? '))
        if int(c) not in range(len(containers) + 1):
            raise
    except:
        click.echo('Invalid input')
        sys.exit(1)

    return containers[(int(c) - 1)]


def desc_service(ecs, cluster, service):
    res = ecs.describe_services(
        cluster=cluster,
        services=[service]
    )
    return res['services'][0]


def desc_task_definition(ecs, taskDefinition):
    res = ecs.describe_task_definition(taskDefinition=taskDefinition)
    return res['taskDefinition']
