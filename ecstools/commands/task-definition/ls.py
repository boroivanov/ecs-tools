import click
import sys

from botocore.exceptions import ClientError


@click.command(short_help='List tasks definitions families / revisions')
@click.argument('name', required=False)
@click.option('-n', '--num', type=int, default=3, help='Number of results')
@click.option('-A', '--arn', is_flag=True, help='Show ARN')
@click.option('-R', '--repo', is_flag=True, help='Show repo URI for images')
@click.option('-D', '--no-details', is_flag=True, default=False, help='Disable revision details')
@click.pass_context
def cli(ctx, name, arn, num, no_details, repo):
    """List families / revisions

        |\b
        $ ecs def

        |\b
        $ ecs def <taks-definition-family>

        |\b
        $ ecs def <taks-definition-family>:<revision>
    """
    ecs = ctx.obj['ecs']

    # Print only task definition families by default
    if not name:
        res = ecs.list_task_definition_families()
        dfs = res['families']
        for d in dfs:
            click.echo(d)
        return
    # Loop through revisions and optionally print details
    else:
        # Taks definition revision was specified
        if ':' in name:
            dfs = [name]
        else:
            res = ecs.list_task_definitions(
                familyPrefix=name,
                sort='DESC',
                maxResults=num
            )
            dfs = res['taskDefinitionArns']

        if not arn:
            dfs = map(lambda x: x.split('/')[-1], dfs)

        for d in dfs:
            if no_details:
                click.echo(d)
                continue

            try:
                res = ecs.describe_task_definition(taskDefinition=d)
            except ClientError as e:
                click.echo(e.response['Error']['Message'], err=True)
                sys.exit(1)

            td = res['taskDefinition']
            containers = td['containerDefinitions']
            click.secho('%s cpu: %s memory: %s' %
                        (d, td.get('cpu', '-'), td.get('memory', '-')), fg='blue')

            for c in containers:
                image = (repo and c['image'] or c['image'].split('/')[-1])
                click.echo('  - %s %s %s %s' %
                           (
                               c['name'],
                               c.get('cpu', '-'),
                               c.get('memory', '-'),
                               image
                           )
                           )
