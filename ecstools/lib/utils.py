import click
import time
import sys

from botocore.exceptions import ClientError

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
            try:
                response = ecs.describe_services(
                    cluster=cluster,
                    services=[service]
                )
                s = response['services'][0]
            except ClientError as e:
                if e.response['Error']['Code'] == 'ClusterNotFoundException':
                    click.echo('Cluster not found.', err=True)
                else:
                    click.echo(e, err=True)
                sys.exit(1)
            except:
                click.echo('Service not found.', err=True)
                sys.exit(1)

            global idx
            idx = 0

            # Print Service Info
            cls_name = s['clusterArn'].split('/')[-1]
            srv_name = s['serviceName']
            out[idx] = '{} {} deployments:'.format(cls_name, srv_name)

            out[index()] = '\n'

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
                out[index()] = '{:<8} {}  desired: {} running: {} pending: {}'.format(
                    *d_info)

                # Print Container Information
                td = get_task_definition(ecs, d['taskDefinition'])
                containers = td['containerDefinitions']
                for c in containers:
                    out[index()] = '{} - {}'.format(
                        ' ' * 8,
                        c['image'].split('/')[-1]
                    )

            out[index()] = '\n'

            # Print Load Balancer info
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


def get_task_definition(ecs, td_name):
    try:
        res = ecs.describe_task_definition(taskDefinition=td_name)
    except ClientError as e:
        click.echo(e.response['Error']['Message'], err=True)
        sys.exit(1)
    return res['taskDefinition']
