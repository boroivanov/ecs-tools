import sys
import time
import curses
import click

from ecstools.main import version
from ecstools.resources.service import Service
from ecstools.resources.task_definition import TaskDefinition
from ecstools.lib.config import config


COLOR_MAP = {
    'NO_COLOR': 0,
    'BLUE': 1,
    'GREEN': 2,
    'RED': 3,
    'YELLOW': 4,
}


def index_generator():
    i = 0
    while True:
        yield i
        i = i + 1


def init_curses_colors():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(COLOR_MAP['NO_COLOR'], -1, -1)
    curses.init_pair(COLOR_MAP['BLUE'], curses.COLOR_BLUE, -1)
    curses.init_pair(COLOR_MAP['GREEN'], curses.COLOR_GREEN, -1)
    curses.init_pair(COLOR_MAP['RED'], curses.COLOR_RED, -1)
    curses.init_pair(COLOR_MAP['YELLOW'], curses.COLOR_YELLOW, -1)


def monitor_deployment(ecs, elbv2, cluster, services, interval=5,
                       exit_on_complete=False):
    """
    Reprint service and deployments info
    """
    start_time = time.time()
    if not isinstance(services, list):
        services = [services]

    scr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    init_curses_colors()

    try:
        while True:
            index = index_generator()
            gmt, elapsed = get_elapsed_time(start_time)

            header = next(index)
            scr.addstr(header, 0, f'Elapsed: {elapsed}'
                       f'  Exit on Complete: {exit_on_complete}')
            scr.addstr(header, curses.COLS-14, f'version {version}')
            scr.addstr(next(index), 0, '')

            print_deployment_info(index, scr, ecs, elbv2, cluster,
                                  services, exit_on_complete)
            scr.refresh()
            scr.clear()
            time.sleep(1)
    except KeyboardInterrupt:
        sys.exit(0)
    finally:
        curses.echo()
        curses.nocbreak()
        curses.endwin()


def print_deployment_info(index, scr, ecs, elbv2, cluster, services,
                          exit_on_complete):
    statuses = {}
    for service in services:
        srv = Service(ecs, None, cluster, service)
        tg = get_load_balancer_info(elbv2, srv)

        print_service_info(index, scr, srv, tg)
        status = print_group_deployment_info(ecs, index, scr, srv)
        statuses[service] = status
        scr.addstr(next(index), 0, '')

        e = srv.events(1)[0]
        date = e['createdAt'].replace(microsecond=0)
        scr.addstr(next(index), 4, f'{date} {e["message"]}',
                   curses.A_DIM)
        scr.addstr(next(index), 0, '')
        scr.addstr(next(index), 0, '')

    scr.addstr(next(index), 0, f'\nCtrl-C to quit the watcher.'
               ' No deployments will be interrupted.')

    del srv

    if deployment_completed(index, scr, statuses, exit_on_complete):
        sys.exit('All deployments completed.')


def print_service_info(index, scr, srv, tg):
    tg_states = ''
    lb_states_color = COLOR_MAP['NO_COLOR']
    if tg is not None:
        tg_states = f'  Load Balancer: [ {tg["states"]} ]'

        if 'draining' in tg_states or 'initial' in tg_states:
            lb_states_color = COLOR_MAP['YELLOW']
        elif 'unhealthy' in tg_states:
            lb_states_color = COLOR_MAP['RED']

    srv_info = f'{srv.cluster()} {srv.name()}  {srv.running_count()}/' \
        f'{srv.desired_count()}'

    line = next(index)
    scr.addstr(line, 0, srv_info, curses.A_BOLD)
    scr.addstr(line, len(srv_info)+1, tg_states,
               curses.color_pair(lb_states_color))


def print_group_deployment_info(ecs, index, scr, srv):
    for d in srv.deployments():
        color = COLOR_MAP['GREEN']
        status = 'Completed '
        if d['runningCount'] < d['desiredCount']:
            color = COLOR_MAP['YELLOW']
            status = 'InProgress'

        scr.addstr(next(index), 4, f'{status} {d["id"]}'
                   f' Running: {d["runningCount"]}'
                   f' Desired: {d["desiredCount"]}'
                   f' Pending: {d["pendingCount"]}', curses.color_pair(color))

        td = TaskDefinition(ecs, d['taskDefinition'])
        for image in td.images():
            # del image['repo']
            # scr.addstr(next(index), 8, f'- {image}')
            scr.addstr(next(index), 8, f'- CONTAINER: {image["container"]}'
                       f' IMAGE: {image["image"]} TAG: {image["tag"]}')
    return deployment_status(srv, d)


def get_load_balancer_info(elbv2, srv):
    for lb in srv.load_balancers():
        if 'targetGroupArn' in lb:
            return describe_target_group_info(elbv2, lb)
    return None


def describe_target_group_info(elbv2, lb):
    targets = elbv2.describe_target_health(TargetGroupArn=lb['targetGroupArn'])

    states = target_health_states(targets['TargetHealthDescriptions'])

    summary = {
        'group': lb['targetGroupArn'].split('/')[-2],
        'container': lb['containerName'],
        'port': lb['containerPort'],
        'states': ' '.join(['{}: {}'.format(k, v) for k, v in states.items()]),
        'healthy': all_containers_are_healthy(states)
    }
    return summary


def target_health_states(target_health_descriptions):
    states = {}
    for t in target_health_descriptions:
        state = t['TargetHealth']['State']
        if state in states:
            states[state] += 1
        else:
            states[state] = 1
    return states


def all_containers_are_healthy(states):
    return all([k == 'healthy' for k in states])


def deployment_status(service, deployment):
    status = 'InProgress'
    if len(service.deployments()) == 1:
        status = 'Completed'
    if deployment['runningCount'] != deployment['desiredCount']:
        status = 'InProgress'
    return status


def get_elapsed_time(start_time):
    elapsed_time = time.time() - start_time
    gmt = time.gmtime(elapsed_time)
    elapsed = time.strftime("%H:%M:%S", gmt)
    return gmt, elapsed


def deployment_completed(index, scr, statuses, exit_on_complete):
    if exit_on_complete:
        if all([x == 'Completed' for x in statuses.values()]):
            scr.addstr(next(index), 0, 'All deployments completed.',
                       curses.A_STANDOUT)
            return True
    return False


def merge_two_dicts(x, y):
    z = x.copy()
    z.update(y)
    return z


def get_group_services(service):
    try:
        if service in config['service-group']:
            services = config['service-group'][service].split(' ')
            return services
        else:
            click.echo('Error: Service group not in config file.')
            sys.exit(1)
    except KeyError:
        click.echo('Error: Section "service-group" not in config file.')
        sys.exit(1)
