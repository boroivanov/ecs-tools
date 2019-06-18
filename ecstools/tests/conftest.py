import pytest
import boto3
from click.testing import CliRunner
from moto import mock_ecs


@pytest.yield_fixture(scope='session')
def runner():
    """
    Setup a Python Click cli runner, this gets executed for each test function.
    """
    yield CliRunner()


@pytest.yield_fixture(scope='session', autouse=True)
def ecs():
    """
    Starts moto ecs server. Creates ecs mock resources. Auto uses the setup
    across all test functions.
    See https://github.com/spulec/moto/issues/620#issuecomment-224339087
    """
    mock_ecs().start()
    conn = boto3.client('ecs', region_name='us-east-1')

    conn.create_cluster(clusterName='production')
    conn.create_cluster(clusterName='staging')
    conn.create_cluster(clusterName='development')

    for service in ['app2', 'worker1', 'app1']:
        # Create task definitions revisions
        for n in range(1, 4):
            conn.register_task_definition(
                family='production-' + service,
                containerDefinitions=create_container_definitions('app1'),
            )

        conn.create_service(
            cluster='production',
            serviceName=service,
            taskDefinition='production-' + service,
            desiredCount=1
        )

    yield
    mock_ecs().stop()


def create_container_definitions(image):
    img_uri = '123456789012.dkr.ecr.us-east-1.amazonaws.com/' + image + ':v0.1'
    return [
        {
            'name': image,
            'image': img_uri,
            'command': ['bash', '-c', 'start'],
            'portMappings': [
                {
                    'hostPort': 80,
                    'protocol': 'tcp',
                    'containerPort': 80
                }
            ],
            'environment': [
                {
                    'name': 'TEST',
                    'value': '123'
                },
                {
                    'name': 'ENV',
                    'value': 'production'
                },
                {
                    'name': 'ROLE',
                    'value': 'webserver'
                },
                {
                    'name': 'KEY',
                    'value': 'asdf'
                }
            ],
            'essential': True
        }
    ]
