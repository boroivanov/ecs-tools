import sys
import time
import curses

from ecstools.resources.service import Service


def index_generator():
    i = 0
    while True:
        yield i
        i = i + 1


def monitor_deployment(ecs, elbv2, cluster, services, interval=5,
                       exit_on_complete=False):
    """
    Reprint service and deployments info
    """
    srv_len = len(max(services, key=len))
    start_time = time.time()
    if not isinstance(services, list):
        services = [services]

    scr = curses.initscr()
    curses.noecho()
    curses.cbreak()

    try:
        while True:
            index = index_generator()
            gmt, elapsed = get_elapsed_time(start_time)

            scr.addstr(next(index), 0, f'Elapsed: {elapsed}')
            if gmt.tm_sec % interval == 0:
                scr.addstr(next(index), 0, '\n')
                print_deployment_info(index, scr, ecs, elbv2, cluster,
                                      services, srv_len, exit_on_complete)
            scr.refresh()
            time.sleep(1)
    finally:
        curses.echo()
        curses.nocbreak()
        curses.endwin()


def print_deployment_info(index, scr, ecs, elbv2, cluster, services,
                          srv_len, exit_on_complete):
    statuses = {}
    for service in services:
        srv = Service(ecs, None, cluster, service)
        status = print_group_deployment_info(
            index, scr, ecs, elbv2, srv, srv_len)
        statuses[service] = status

    scr.addstr(next(index), 0, f'\nCtrl-C to quit the watcher.'
               ' No deployments will be interrupted.')

    if deployment_completed(index, scr, statuses, exit_on_complete):
        sys.exit(0)

    del srv


def print_group_deployment_info(index, scr, ecs, elbv2, srv, srv_len):
    for d in srv.deployments()[:1]:
        d_info = {
            'cluster': srv.cluster(),
            'service': srv.name(),
            'runningCount': d['runningCount'],
            'desiredCount': d['desiredCount'],
            'pad': srv_len,
            'status': 'InProgress',
        }
        output_template = '{status:11} {cluster} {service:{pad}}  ' \
            '{runningCount}/{desiredCount}'

        d_info['status'] = deployment_status(srv, d)
        d_info, output_template = print_load_balancer_info(elbv2, srv, d_info,
                                                           output_template)
        scr.addstr(next(index), 0, output_template.format(**d_info))

    return d_info['status']


def print_load_balancer_info(elbv2, srv, d_info, output_template):
    for lb in srv.load_balancers():
        if 'targetGroupArn' in lb:
            tg_info = describe_target_group_info(elbv2, lb)
            d_info = merge_two_dicts(d_info, tg_info)
            output_template = '{status:11} {cluster} {service:{pad}}  ' \
                '{runningCount}/{desiredCount}  LB: [{states}]'
            if not tg_info['healthy']:
                d_info['status'] = 'InProgress'
    return d_info, output_template


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
            scr.addstr(next(index), 0, 'All deployments completed.')
            return True
    return False


def merge_two_dicts(x, y):
    z = x.copy()
    z.update(y)
    return z
