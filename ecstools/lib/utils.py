import time
from reprint import output

from ecstools.resources.service import Service
from ecstools.resources.task_definition import TaskDefinition

idx = 0


def index():
    global idx
    idx += 1
    return idx


def monitor_deployment(ecs, elbv2, cluster, service, interval=5):
    """
    Reprint service and deployments info
    """
    with output(initial_len=20, interval=0) as out:
        while True:
            global idx
            idx = 0

            srv = Service(ecs, None, cluster, service)

            out[idx] = '{} {} deployments:'.format(srv.cluster(), srv.name())
            out[index()] = '\n'

            print_deployment_info(idx, out, ecs, srv)
            out[index()] = '\n'
            print_loadbalancer_into(idx, out, elbv2, srv)
            print_ecs_events(idx, out, srv)

            del srv
            time.sleep(interval)


def print_deployment_info(idx, out, ecs, srv):
    for d in srv.deployments():
        d_info = (
            d['status'],
            d['taskDefinition'].split('/')[-1],
            d['desiredCount'],
            d['runningCount'],
            d['pendingCount']
        )
        idx += srv.deployments().index(d)
        out[index()] = '{:<8} {}  desired: {} running: {} ' \
            'pending: {}'.format(
            *d_info)

        # Print Container Information
        td = TaskDefinition(ecs, d['taskDefinition'])
        for c in td.containers():
            out[index()] = '{} - {}'.format(
                ' ' * 8,
                c['image'].split('/')[-1]
            )
    out[index()] = '\n'


def print_loadbalancer_into(idx, out, elbv2, srv):
    for lb in srv.load_balancers():
        if 'targetGroupArn' in lb:
            tg_info = describe_target_group_info(elbv2, lb)
            out[index()] = 'Target Group: {group}  ' \
                '{container} {port} {states}'.format(
                **tg_info)
    out[index()] = '\n'


def print_ecs_events(idx, out, srv):
    events = srv.events(2)
    for e in events:
        idx += events.index(e)
        createdAt = e['createdAt'].replace(microsecond=0)
        out[index()] = '{} {}'.format(createdAt, e['message'])


def describe_target_group_info(elbv2, lb):
    targets = elbv2.describe_target_health(TargetGroupArn=lb['targetGroupArn'])

    states = target_health_states(targets['TargetHealthDescriptions'])

    summary = {
        'group': lb['targetGroupArn'].split('/')[-2],
        'container': lb['containerName'],
        'port': lb['containerPort'],
        'states': ' '.join(['{}: {}'.format(k, v) for k, v in states.items()])
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
