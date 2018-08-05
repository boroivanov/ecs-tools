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
    confirm_input('Do you want to deploy your changes? ')
    td_dict = srv.update_container_environment(container, new_envs)
    td = srv.register_task_definition(td_dict, verbose=True)
    srv.deploy_task_definition(td, verbose=True)

    click.echo()
    utils.monitor_deployment(ecs, elbv2, cluster, service,
                             exit_on_complete=True)


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
        container_number = ask_container_number(containers)
        return containers[(int(container_number) - 1)]
    return containers[0]


def ask_container_number(containers):
    try:
        container_number = int(six.moves.input('#? '))
        if int(container_number) not in range(1, len(containers) + 1):
            raise ValueError()
    except ValueError:
        click.echo('Invalid input')
        sys.exit(1)
    return container_number


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
        key, value = pair.split('=', 1)
        envs, matched = update_env(envs, key, value)
        if not matched:
            envs = add_env(envs, key, value)
    return envs


def add_env(envs, key, value):
    click.echo('+ %s=%s' % (key, value))
    envs.append({'name': key, 'value': value})
    return envs


def update_env(envs, key, value):
    matched = False
    for env in envs:
        if key == env['name']:
            print_env_value_diff(env, key, value)
            env['value'] = value
            matched = True
            break
    return envs, matched


def print_env_value_diff(env, key, value):
    if value != env['value']:
        click.echo('- %s=%s' % (env['name'], env['value']))
        click.echo('+ ', nl=False)
    click.echo('%s=%s' % (key, value))


def print_environment_variables(envs):
    sorted_envs = sorted(envs, key=lambda k: k['name'])
    for e in sorted_envs:
        click.echo('%s=%s' % (e['name'], e['value']))
    sys.exit(0)
