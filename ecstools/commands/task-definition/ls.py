import click

from ecstools.resources.task_definition import TaskDefinition


@click.command(short_help='List tasks definitions families / revisions')
@click.argument('name', required=False)
@click.option('-n', '--num', type=int, default=3, help='Number of results')
@click.option('-A', '--arn', is_flag=True, help='Show ARN')
@click.option('-R', '--repo', is_flag=True, help='Show repo URI for images')
@click.option('-D', '--no-details', is_flag=True, default=False,
              help='Disable revision details')
@click.pass_context
def ls(ctx, name, arn, num, no_details, repo):
    """List families / revisions

        |\b
        $ ecs def

        |\b
        $ ecs def <task-definition-family>

        |\b
        $ ecs def <task-definition-family>:<revision>
    """
    ecs = ctx.obj['ecs']

    if not name:
        print_task_definition_families(ecs)
    else:
        print_task_definition_revisions(ecs, name, arn, num, no_details, repo)


def print_task_definition_families(ecs):
    res = ecs.list_task_definition_families()
    for family in sorted(res['families']):
        click.echo(family)


def print_task_definition_revisions(ecs, name, arn, num, no_details, repo):
    # Task definition revision was specified
    if ':' in name:
        definitions = [name]
    else:
        res = ecs.list_task_definitions(
            familyPrefix=name,
            sort='DESC',
            maxResults=num
        )
        definitions = res['taskDefinitionArns']

    if not arn:
        definitions = map(lambda x: x.split('/')[-1], definitions)

    print_task_definition_info(ecs, repo, definitions, no_details)


def print_task_definition_info(ecs, repo, definitions, no_details):
    for td_name in sorted(definitions):
        if no_details:
            click.echo(td_name)
            continue

        td = TaskDefinition(ecs, td_name)
        click.secho('%s cpu: %s memory: %s' % (td.revision(),
                                               td.cpu(),
                                               td.memory()
                                               ), fg='blue')
        print_containers_info(repo, td.containers())


def print_containers_info(repo, containers):
    for c in containers:
        # Include the repo URI if the repo flag is set
        image = (repo and c['image'] or c['image'].split('/')[-1])
        click.echo('  - %s %s %s %s' % (c['name'],
                                        c.get('cpu', '-'),
                                        c.get('memory', '-'),
                                        image))
