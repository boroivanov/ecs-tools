import time
from reprint import output

from ecstools.resources.service import Service
from ecstools.resources.task_definition import TaskDefinition


def index_generator():
    i = 0
    while True:
        yield i
        i = i + 1


def monitor_deployment(ecs, elbv2, cluster, services, interval=5):
    """
    Reprint service and deployments info
    """
    srv_len = len(max(services, key=len))
    start_time = time.time()

    with output(initial_len=20, interval=0) as out:
        while True:
            index = index_generator()

            elapsed_time = time.time() - start_time
            gmt = time.gmtime(elapsed_time)
            elapsed = time.strftime("%H:%M:%S", gmt)
            out[next(index)] = 'Elapsed: {}'.format(elapsed)

            if gmt.tm_sec % interval == 0:
                if isinstance(services, list):
                    for service in services:
                        srv = Service(ecs, None, cluster, service)
                        print_group_deployment_info(
                            index, out, ecs, elbv2, srv, srv_len)
                else:
                    srv = Service(ecs, None, cluster, services)
                    out[next(index)] = '{} {} deployments:'.format(
                        srv.cluster(), srv.name())
                    out[next(index)] = '\n'

                    print_deployment_info(index, out, ecs, srv)
                    out[next(index)] = '\n'
                    print_loadbalancer_into(index, out, elbv2, srv)
                    print_ecs_events(index, out, srv)

                del srv
            time.sleep(1)


def print_group_deployment_info(index, out, ecs, elbv2, srv, srv_len):
    for d in srv.deployments()[:1]:
        d_info = {
            'cluster': srv.cluster(),
            'service': srv.name(),
            'runningCount': d['runningCount'],
            'desiredCount': d['desiredCount'],
            'states': 'n/a',
            'pad': srv_len
        }
        for lb in srv.load_balancers():
            if 'targetGroupArn' in lb:
                tg_info = describe_target_group_info(elbv2, lb)
                d_info = merge_two_dicts(d_info, tg_info)

        out[next(index)] = '{cluster} {service:{pad}}  ' \
            '{runningCount}/{desiredCount}  LB: [{states}]'.format(**d_info)


def print_deployment_info(index, out, ecs, srv):
    for d in srv.deployments():
        d_info = (
            d['status'],
            d['taskDefinition'].split('/')[-1],
            d['desiredCount'],
            d['runningCount'],
            d['pendingCount']
        )
        out[next(index)] = '{:<8} {}  desired: {} running: {} ' \
            'pending: {}'.format(
            *d_info)

        # Print Container Information
        td = TaskDefinition(ecs, d['taskDefinition'])
        for c in td.containers():
            out[next(index)] = '{} - {}'.format(
                ' ' * 8,
                c['image'].split('/')[-1]
            )
    out[next(index)] = '\n'


def print_loadbalancer_into(index, out, elbv2, srv):
    for lb in srv.load_balancers():
        if 'targetGroupArn' in lb:
            tg_info = describe_target_group_info(elbv2, lb)
            out[next(index)] = 'Target Group: {group}  ' \
                '{container} {port} {states}'.format(
                **tg_info)
    out[next(index)] = '\n'


def print_ecs_events(index, out, srv):
    events = srv.events(2)
    for e in events:
        createdAt = e['createdAt'].replace(microsecond=0)
        out[next(index)] = '{} {}'.format(createdAt, e['message'])


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


def merge_two_dicts(x, y):
    z = x.copy()
    z.update(y)
    return z
