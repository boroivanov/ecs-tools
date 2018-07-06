import sys
import click

from botocore.exceptions import ClientError


class TaskDefinition(object):
    def __init__(self, ecs, taskDefinition):
        self.ecs = ecs
        self.taskDefinition = taskDefinition
        self.td = self.describe_task_definition()

    def describe_task_definition(self):
        try:
            params = {'taskDefinition': self.taskDefinition}
            res = self.ecs.describe_task_definition(**params)
        except ClientError as e:
            click.echo(e.response['Error']['Message'], err=True)
            sys.exit(1)
        return res['taskDefinition']

    def arn(self):
        return self.td['taskDefinitionArn']

    def name(self):
        return self.td['family']

    def revision(self):
        return self.td['family'] + ':' + str(self.td['revision'])

    def containers(self):
        return self.td['containerDefinitions']

    def images(self):
        """Returns a list of image properties dicts"""
        return [self.image(x) for x in self.containers()]

    def image(self, container):
        """Returns an image properties dict"""
        if isinstance(container, str):
            for c in self.containers():
                if c['name'] == container:
                    image = c['image']
                    container_name = c['name']
        elif isinstance(container, int):
            image = self.containers()[container]['image']
            container_name = self.containers()[container]['name']
        else:
            image = container['image']
            container_name = container['name']
        return {
            'container': container_name,
            'repo': self._image_repo(image),
            'image': self._image_name(image),
            'tag': self._image_tag(image)
        }

    def _image_repo(self, image):
        """Strips image repo from image URI"""
        return image.split('/')[0]

    def _image_name(self, image):
        """Strips image name from image URI"""
        return image.split('/')[1].split(':')[0]

    def _image_tag(self, image):
        """Strips image tag from image URI"""
        tag = ''
        if ':' in image:
            tag = image.split(':')[-1:][0]
        return tag

    def copy_task_definition(self):
        """
        Copy task definition and cleanup aws reserved params.
        """
        aws_reserved_params = ['status',
                               'compatibilities',
                               'taskDefinitionArn',
                               'revision',
                               'requiresAttributes'
                               ]
        new_td = self.td.copy()

        for k in aws_reserved_params:
            del new_td[k]
        return new_td
