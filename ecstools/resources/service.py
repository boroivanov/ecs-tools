import sys
import click

from botocore.exceptions import ClientError

from ecstools.resources.task_definition import TaskDefinition
from ecstools.resources.ecr import Ecr


class Service(object):
    def __init__(self, ecs, ecr, cluster, service):
        self.ecs = ecs
        self.ecr = ecr
        self._cluster = cluster
        self._service_name = service
        self._service = self._describe_service()
        self._td = TaskDefinition(self.ecs, self._service['taskDefinition'])

    def service(self):
        return self._service

    def name(self):
        return self._service_name

    def cluster(self):
        return self._cluster

    def deployments(self):
        return self._service['deployments']

    def load_balancers(self):
        return self._service['loadBalancers']

    def events(self, number):
        return self._service['events'][:number]

    def task_definition(self):
        return self._td

    def containers(self):
        return self.task_definition().containers()

    def images(self):
        return self.task_definition().images()

    def deploy_tags(self, tags, count, verbose):
        """
        Redeploy the current task definition if all tags are already deployed.
        Otherwise, deploy the updated task definition with the new tags.
        """
        if self._are_images_in_current_task_definition(tags):
            self._redeploy_current_task_definition(count, verbose)
            return

        td_dict = self.update_task_definition_images(tags)
        td = self.register_task_definition(td_dict, verbose)
        self.deploy_task_definition(td.name(), verbose, count)

    def deploy_task_definition(self, taskDefinition, verbose, count=None):
        if verbose:
            click.secho('Deploying %s to %s %s...' % (
                self.task_definition().revision(),
                self.cluster(),
                self.name()),
                fg='blue'
            )
        params = {
            'cluster': self.cluster(),
            'service': self.name(),
            'taskDefinition': self.task_definition().name(),
            'forceNewDeployment': True
        }
        if count:
            params['desiredCount'] = count
        self.update_service(**params)

    def _describe_service(self):
        try:
            response = self.ecs.describe_services(
                cluster=self.cluster(),
                services=[self.name()]
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

    def update_service(self, **params):
        try:
            self.ecs.update_service(**params)
        except ClientError as e:
            click.echo(e.response['Error']['Message'], err=True)
            sys.exit(1)

    def update_task_definition_images(self, tags):
        """
        Creates a copy of the current task definition.
        Validates the new tags are in the repo.
        Updates the images in the copied task definition dict.
        Returns an updated task definition dict.
        """
        td_dict = self.task_definition().copy_task_definition()
        ecr = Ecr(self.ecr)

        for tag in tags:
            index = tags.index(tag)
            current = self.task_definition().image(index)
            repo_uri = '{}/{}'.format(current['repo'], current['image'])
            image_uri = '{}:{}'.format(repo_uri, tag)
            ecr.verify_image_in_ecr(current['image'], tag)
            td_dict['containerDefinitions'][index]['image'] = image_uri
        return td_dict

    def update_container_environment(self, container, environment):
        """
        Creates a copy of the current task definition.
        Updates the environment variables for the specified container.
        Returns an updated task definition dict.
        """
        td_dict = self.task_definition().copy_task_definition()

        for c in td_dict['containerDefinitions']:
            if c['name'] == container['name']:
                c['environment'] = environment

        return td_dict

    def register_task_definition(self, td_dict, verbose):
        """
        Register a new task definition.
        Returns a new task definition object.
        """
        try:
            result = self.ecs.register_task_definition(**td_dict)
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDeniedException':
                click.echo(e, err=True)
            else:
                click.echo(e, err=True)
            sys.exit(1)

        td_rev = result['taskDefinition']['taskDefinitionArn'].split('/')[-1]
        new_td = TaskDefinition(self.ecs, td_rev)

        if verbose:
            click.secho('Registered new task definition: %s' %
                        new_td.revision(), fg='green')
        return new_td

    def _redeploy_current_task_definition(self, count, verbose):
        if verbose:
            click.secho(
                'The images are already in the current task definition.')
            click.secho(('Forcing a new deployment of %s' %
                         self.task_definition().revision()), fg='white')
        self.deploy_task_definition(self.task_definition().revision(),
                                    verbose, count)

    def _are_images_in_current_task_definition(self, tags):
        current_tags = [i['tag'] for i in self.images()]
        return all([x in current_tags for x in tags])
