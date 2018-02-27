import time

from reprint import output

idx = 0


def index():
    global idx
    idx += 1
    return idx


def monitor_deployment(ecs, elbv2, cluster, service):
    # Reprint service and deployments info
    with output(initial_len=20, interval=0) as out:
        while True:
            response = ecs.describe_services(
                cluster=cluster,
                services=[service]
            )
            s = response['services'][0]

            global idx
            idx = 0

            # # Print Service Info
            cls_name = s['clusterArn'].split('/')[-1]
            def_name = s['taskDefinition'].split('/')[-1]
            general_info = (cls_name, s['serviceName'], def_name)
            counts = (s['desiredCount'], s['runningCount'], s['pendingCount'])
            srv_info = general_info + counts
            out[idx] = '{} {:<24}  {}  desired: {} running: {} pending: {}'.format(
                *srv_info)

            out[index()] = '\n'
            out[index()] = 'Deployments:'

            # # Print Deployments Info
            for d in s['deployments']:
                d_info = (
                    d['status'],
                    d['taskDefinition'].split('/')[-1],
                    d['desiredCount'],
                    d['runningCount'],
                    d['pendingCount']
                )
                idx += s['deployments'].index(d)
                out[index()] = '\t\t{:<31} {}  desired: {} running: {} pending: {}'.format(
                    *d_info)

            out[index()] = '\n'

            for lb in s['loadBalancers']:
                tgs_state = {}
                if 'targetGroupArn' in lb:
                    targets = elbv2.describe_target_health(
                        TargetGroupArn=lb['targetGroupArn'])

                    for t in targets['TargetHealthDescriptions']:
                        state = t['TargetHealth']['State']
                        if state in tgs_state:
                            tgs_state[state] += 1
                        else:
                            tgs_state[state] = 1
                    group = lb['targetGroupArn'].split('/')[-2]
                    container = lb['containerName']
                    port = lb['containerPort']
                    states = ' '.join(['{}: {}'.format(k, v)
                                       for k, v in tgs_state.items()])
                    out[index()] = 'Target Group: {}  {} {}  {}'.format(
                        group, container, port, states)
            out[index()] = '\n'

            for e in s['events'][:2]:
                idx += s['events'].index(e)
                createdAt = e['createdAt'].replace(microsecond=0)
                out[index()] = '{} {}'.format(createdAt, e['message'])

            time.sleep(2)
