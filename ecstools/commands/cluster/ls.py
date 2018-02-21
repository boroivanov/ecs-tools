import click


@click.command()
@click.option('-A', '--arn', is_flag=True, help='Show ARN')
@click.pass_context
def cli(ctx, arn):
    """List clusters"""
    ecs = ctx.obj['ecs']
    res = ecs.list_clusters()
    clusters = res['clusterArns']

    if not arn:
        clusters = map(lambda x: x.split('/')[-1], clusters)

    for c in clusters:
        click.echo(c)
