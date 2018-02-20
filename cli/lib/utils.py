import time

from reprint import output


def monitor_deployment(ecs, cluster, service):
    # Reprint service and deployments info
    with output(initial_len=25, interval=0) as out:
        while True:
            response = ecs.describe_services(
                cluster=cluster,
                services=[service]
            )
            s = response['services'][0]

            # Print Service Info
            cls_name = s['clusterArn'].split('/')[-1]
            def_name = s['taskDefinition'].split('/')[-1]
            general_info = (cls_name, s['serviceName'], def_name)
            counts = (s['desiredCount'], s['runningCount'], s['pendingCount'])
            srv_info = general_info + counts
            out[0] = '{} {:<24}  {}  desired: {} running: {} pending: {}'.format(
                *srv_info)

            out[1] = '\n'
            out[2] = 'Deployments:'

            # Print Deployments Info
            for d in s['deployments']:
                d_info = (
                    d['status'],
                    d['taskDefinition'].split('/')[-1],
                    d['desiredCount'],
                    d['runningCount'],
                    d['pendingCount']
                )
                index = s['deployments'].index(d) + 3
                out[index] = '\t\t{:<31} {}  desired: {} running: {} pending: {}'.format(
                    *d_info)

            out[(len(s['deployments']) + 4)] = '\n'

            for e in s['events'][:5]:
                index = s['events'].index(e) + len(s['deployments']) + 5
                out[index] = '{} {}'.format(e['createdAt'], e['message'])

            time.sleep(2)
