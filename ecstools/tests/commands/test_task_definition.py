import ecstools.main as main


class TestTaskDefinition(object):
    def test_task_definition_subcommand(self, runner):
        result = runner.invoke(main.cli, ['task-definition'])
        assert result.exit_code == 0

    def test_task_definition_ls(self, runner):
        result = runner.invoke(main.cli, ['task-definition', 'ls'])
        expected = 'production-app1\nproduction-app2\nproduction-worker1\n'
        assert result.output == expected

    # moto list_task_definitions filtering not implemented
    # def test_task_definition_ls_revisions(self, runner):
    #     result = runner.invoke(
    #         main.cli, ['task-definition', 'ls', '-D', 'prod-app1'])
    #     expected = 'prod-app1:3\nprod-app1:2\nprod-app1:1\n'
    #     assert result.output == expected
