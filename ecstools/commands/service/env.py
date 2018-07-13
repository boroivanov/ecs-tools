import click
import sys
import copy
import six

from ecstools.resources.service import Service
import ecstools.lib.utils as utils


@click.command(short_help='Manage environment variables')
@click.argument('cluster', nargs=1)
@click.argument('service', nargs=1)
@click.argument('pairs', nargs=-1)
@click.option('-d', '--delete', is_flag=True,
              help='Delete environment variable')
@click.pass_context
def env(ctx, cluster, service, pairs, delete):
    """Manage environment variables

    |\b
    # List environment variables
    $ ecs service env CLUSTER SERVICE

    # Set environment variables
    $ ecs service env CLUSTER SERVICE KEY1=VALUE1 KEY2=VALUE2 ...
    """
    ecs = ctx.obj['ecs']
    ecr = ctx.obj['ecr']
    elbv2 = ctx.obj['elbv2']
    srv = Service(ecs, ecr, cluster, service)

    click.secho('Current task definition for {} {}: {}'.format(
                cluster, service, srv.task_definition().revision()
                ), fg='blue')

    container = container_selection(srv.task_definition().containers())
    click.secho(('\n==> Container: %s' % container['name']), fg='white')

    # Just print env vars if none were passed
    if len(pairs) == 0:
        print_environment_variables(container['environment'])

    new_envs = update_environment_variables(container, pairs, delete)

    if new_envs == container['environment']:
        click.echo('\nNo updates')
        sys.exit(0)

    click.echo()
    confirm_input('Do you want to create a new task definition revision? ')
    td_dict = srv.update_container_environment(container, new_envs)
    td = srv.register_task_definition(td_dict)

    confirm_input('Do you want to deploy your changes? ')
    srv.deploy_task_definition(td)

    click.echo()
    utils.monitor_deployment(ecs, elbv2, cluster, service)


def confirm_input(text):
    try:
        c = six.moves.input(text)
        if c not in ['yes', 'Yes', 'y', 'Y']:
            raise ValueError()
    except ValueError:
        sys.exit(0)


def validate_pairs(pairs):
    for pair in pairs:
        if len(pair.split('=', 1)) != 2:
            click.echo('Not a valid pair: %s' % pair)
            sys.exit(1)


def container_selection(containers):
    if len(containers) > 1:
        for c in containers:
            click.echo('%s) %s' % (containers.index(c) + 1, c['name']))

        try:
            c = int(six.moves.input('#? '))
            if int(c) not in range(1, len(containers) + 1):
                raise ValueError()
        except ValueError:
            click.echo('Invalid input')
            sys.exit(1)

        return containers[(int(c) - 1)]
    return containers[0]


def update_environment_variables(container, pairs, delete):
    envs = copy.deepcopy(container['environment'])
    if delete:
        return delete_environment_variables(pairs, envs)
    else:
        return set_environment_variables(pairs, envs)


def delete_environment_variables(pairs, envs):
    for pair in pairs:
        key = pair.split('=', 1)[0]
        for e in envs:
            if key == e['name']:
                click.echo('- %s=%s' % (e['name'], e['value']))
                envs.remove(e)
    return envs


def set_environment_variables(pairs, envs):
    # Update env var if it exist. Otherwise append it.
    validate_pairs(pairs)

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

    return envs


def print_environment_variables(envs):
    sorted_envs = sorted(envs, key=lambda k: k['name'])
    for e in sorted_envs:
        click.echo('%s=%s' % (e['name'], e['value']))
    sys.exit(0)
