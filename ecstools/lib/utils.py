import time

from reprint import output

idx = 0


def index():
    global idx
    idx += 1
    return idx


def monitor_deployment(ecs, cluster, service):
    # Reprint service and deployments info
    with output(initial_len=30, interval=0) as out:
        while True:
            response = ecs.describe_services(
                cluster=cluster,
                services=[service]
            )
            s = response['services'][0]

            global idx
            idx = 0

            # Print Deployment Configuration Info
            min_healthy = s['deploymentConfiguration']['minimumHealthyPercent']
            max_healthy = s['deploymentConfiguration']['maximumPercent']
            out[idx] = 'Deployment Configuration: min: {}% max: {}%'.format(
                min_healthy, max_healthy)
            out[index()] = '\n'

            # # Print Service Info
            cls_name = s['clusterArn'].split('/')[-1]
            def_name = s['taskDefinition'].split('/')[-1]
            general_info = (cls_name, s['serviceName'], def_name)
            counts = (s['desiredCount'], s['runningCount'], s['pendingCount'])
            srv_info = general_info + counts
            out[index()] = '{} {:<24}  {}  desired: {} running: {} pending: {}'.format(
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

            # out[(len(s['deployments']) + 6)] = '\n'
            out[index()] = '\n'

            for e in s['events'][:5]:
                idx += s['events'].index(e)
                out[index()] = '{} {}'.format(e['createdAt'], e['message'])

            time.sleep(2)
