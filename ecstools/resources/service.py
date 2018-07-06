import sys
import click

from botocore.exceptions import ClientError

from ecstools.resources.task_definition import TaskDefinition
from ecstools.resources.ecr import Ecr


class Service(object):
    def __init__(self, ecs, ecr, cluster, service):
        self.ecs = ecs
        self.ecr = ecr
        self.cluster = cluster
        self.service_name = service
        self.service = self._describe_service()
        self.td = TaskDefinition(self.ecs, self.service['taskDefinition'])

    def name(self):
        return self.service_name

    def cluster(self):
        return self.cluster

    def task_definition(self):
        return self.td

    def images(self):
        return self.task_definition().images()

    def deploy_tags(self, tags, count):
        """
        Redeploy the current task definition if all tags are already deployed.
        Otherwise, deploy the updated task definition with the new tags.
        """
        if self._are_images_in_current_task_definition(tags):
            self._redeploy_current_task_definition(count)
            return

        td = self._register_new_task_definition(tags)
        self.deploy_task_definition(td.name(), count)

    def deploy_task_definition(self, taskDefinition, count):
        click.secho('Deploying %s to %s %s...' % (
            self.task_definition().revision(),
            self.cluster,
            self.service_name),
            fg='blue'
        )
        params = {
            'cluster': self.cluster,
            'service': self.service_name,
            'taskDefinition': self.task_definition().name(),
            'forceNewDeployment': True
        }
        if count:
            params['desiredCount'] = count
        self._update_service(**params)

    def _describe_service(self):
        try:
            response = self.ecs.describe_services(
                cluster=self.cluster,
                services=[self.service_name]
            )
            return response['services'][0]
        except ClientError as e:
            if e.response['Error']['Code'] == 'ClusterNotFoundException':
                click.echo('Cluster not found.', err=True)
            else:
                click.echo(e, err=True)
            sys.exit(1)
        except IndexError:
            click.echo('Service not found.', err=True)
            sys.exit(1)

    def _update_service(self, **params):
        try:
            self.ecs.update_service(**params)
        except ClientError as e:
            click.echo(e.response['Error']['Message'], err=True)
            sys.exit(1)

    def _register_new_task_definition(self, tags):
        """
        Creates a copy of the current task definition.
        Validates the new tags are in the repo.
        Updates the images in the copied task definition and registers it.
        Returns a new task definition object.
        """
        td_json = self.task_definition().copy_task_definition()
        ecr = Ecr(self.ecr)

        for tag in tags:
            index = tags.index(tag)
            current = self.task_definition().image(index)
            repo_uri = '{}/{}'.format(current['repo'], current['image'])
            image_uri = '{}:{}'.format(repo_uri, tag)
            ecr.verify_image_in_ecr(current['image'], tag)
            td_json['containerDefinitions'][index]['image'] = image_uri

        result = self.ecs.register_task_definition(**td_json)
        td_rev = result['taskDefinition']['taskDefinitionArn'].split('/')[-1]
        new_td = TaskDefinition(self.ecs, td_rev)

        click.secho('Registered new task definition: %s' %
                    new_td.name(), fg='green')
        return new_td

    def _redeploy_current_task_definition(self, count):
        click.secho('The images are already in the current task definition.')
        click.secho(('Forcing a new deployment of %s' %
                     self.task_definition().revision()), fg='white')
        self.deploy_task_definition(self.task_definition().revision(), count)

    def _are_images_in_current_task_definition(self, tags):
        current_tags = [i['tag'] for i in self.images()]
        return all([x in current_tags for x in tags])
