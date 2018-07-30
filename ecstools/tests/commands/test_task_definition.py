import ecstools.main as main


class TestTaskDefinition(object):
    def test_task_definition_subcommand(self, runner):
        result = runner.invoke(main.cli, ['task-definition'])
        assert result.exit_code == 0

    def test_task_definition_ls(self, runner):
        result = runner.invoke(main.cli, ['task-definition', 'ls'])
        expected = 'production-app1\nproduction-app2\nproduction-worker1\n'
        assert result.output == expected

    def test_task_definition_ls_alias(self, runner):
        result = runner.invoke(main.cli, ['td'])
        expected = 'production-app1\nproduction-app2\nproduction-worker1\n'
        assert result.output == expected

    # moto list_task_definitions filtering not implemented
    def test_task_definition_ls_revisions_no_details(self, runner):
        result = runner.invoke(
            main.cli,
            ['task-definition', 'ls', '-D', 'production-app1']
        )
        expected = 'production-app1:1\nproduction-app1:2\n' \
            'production-app1:3\nproduction-app2:1\nproduction-app2:2\n' \
            'production-app2:3\nproduction-worker1:1\nproduction-worker1:2\n' \
            'production-worker1:3\n'
        assert result.output == expected

    # moto list_task_definitions container info not implemented
    def test_task_definition_ls_single_revision(self, runner):
        result = runner.invoke(
            main.cli,
            ['task-definition', 'ls', 'production-app1:1']
        )
        expected = ''
        assert result.output == expected

    def test_task_definition_ls_single_revision_no_details(self, runner):
        result = runner.invoke(
            main.cli,
            ['task-definition', 'ls', '-D', 'production-app1:1']
        )
        expected = 'production-app1:1\n'
        assert result.output == expected
