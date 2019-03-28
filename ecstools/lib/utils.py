import sys
import time
import curses

from ecstools.resources.service import Service
from ecstools.resources.task_definition import TaskDefinition


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

            scr.addstr(next(index), 0, f'Elapsed: {elapsed}'
                       f'  Exit on Complete: {exit_on_complete}')
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
    if tg is not None:
        tg_states = f'  Load Balancer: [ {tg["states"]} ]'

    scr.addstr(next(index), 0, f'{srv.cluster()} {srv.name()}'
               f'  {srv.running_count()}/{srv.desired_count()}{tg_states}',
               curses.A_BOLD)


def print_group_deployment_info(ecs, index, scr, srv):
    for d in srv.deployments():
        scr.addstr(next(index), 4, f'{d["id"]} Running: {d["runningCount"]}'
                   f' Desired: {d["desiredCount"]}'
                   f' Pending: {d["pendingCount"]}', curses.A_LOW)

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
