import sys
import click

from botocore.exceptions import ClientError


class Ecr(object):
    def __init__(self, ecr):
        self.ecr = ecr

    def verify_image_in_ecr(self, image, tag):
        try:
            self.ecr.describe_images(
                repositoryName=image,
                imageIds=[
                    {
                        'imageTag': tag
                    },
                ],
                filter={
                    'tagStatus': 'TAGGED'
                }
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'ImageNotFoundException':
                click.echo('Image not found: %s' % e, err=True)
            else:
                click.echo(e, err=True)
            sys.exit(1)
