import click


@click.command()
@click.argument('cluster')
@click.option('-A', '--arn', is_flag=True, help='Show ARN')
@click.pass_context
def cli(ctx, cluster, arn):
    """List services"""
    ecs = ctx.obj['ecs']
    response = ecs.list_services(cluster=cluster, maxResults=100)
    services = response['serviceArns']
    while True:
        if 'nextToken' not in response:
            break
        response = ecs.list_services(
            cluster=cluster,
            maxResults=100,
            nextToken=response['nextToken']
        )
        services += response['serviceArns']

    if not arn:
        services = sorted(map(lambda x: x.split('/')[-1], services))

    for s in services:
        click.echo('%s' % s)
