import ecstools.main as main


class TestService(object):
    def test_service_subcommand(self, runner):
        result = runner.invoke(main.cli, ['service'])
        assert result.exit_code == 0

    def test_service_ls(self, runner):
        result = runner.invoke(main.cli, ['service', 'ls', 'production'])
        expected = 'app1\napp2\nworker1\n'
        assert result.output == expected

    def test_service_ls_alias(self, runner):
        result = runner.invoke(main.cli, ['ls', 'production'])
        expected = 'app1\napp2\nworker1\n'
        assert result.output == expected

    # TODO: moto list_task_definitions container info not implemented
    # the tests lists only the first service. However, all services should be
    # listed
    def test_service_ls_all_stats(self, runner):
        result = runner.invoke(main.cli, ['service', 'ls', 'production', '-a'])
        expected = 'app1' + (' ' * 29) + \
            'production-app1:3' + (' ' * 34) + '0/1   '
        assert result.output == expected

    # TODO: moto raise exceptions not implemented
    # def test_service_ls_cluster_not_found(self, runner):
    #     result = runner.invoke(main.cli, ['service', 'ls', 'nonexistent'])
    #     assert result.exit_code == 1
    #     expected = 'Cluster not found.'
    #     assert result.output == expected

    def test_service_env(self, runner):
        result = runner.invoke(
            main.cli,
            ['service', 'env', 'production', 'app1']
        )
        expected = 'Current task definition for production app1: ' + \
            'production-app1:3\n\n==> Container: app1\nENV=production\n' + \
            'KEY=asdf\nROLE=webserver\nTEST=123\n\n'
        assert result.output == expected

    def test_service_env_alias(self, runner):
        result = runner.invoke(main.cli, ['env', 'production', 'app1'])
        expected = 'Current task definition for production app1: ' + \
            'production-app1:3\n\n==> Container: app1\nENV=production\n' + \
            'KEY=asdf\nROLE=webserver\nTEST=123\n\n'
        assert result.output == expected

    def test_service_env_set_var(self, runner):
        result = runner.invoke(
            main.cli,
            ['service', 'env', 'production', 'app1', 'KEY_ADD=VALUE']
        )
        expected = '+ KEY_ADD=VALUE'
        assert expected in result.output

    def test_service_env_replace_var(self, runner):
        result = runner.invoke(
            main.cli,
            ['service', 'env', 'production', 'app1', 'TEST=1234']
        )
        expected = '- TEST=123\n+ TEST=1234'
        assert expected in result.output

    def test_service_env_delete_var(self, runner):
        result = runner.invoke(
            main.cli,
            ['service', 'env', 'production', 'app1', 'TEST=123', '-d']
        )
        expected = '- TEST=123'
        assert expected in result.output

    def test_service_env_no_updates(self, runner):
        result = runner.invoke(
            main.cli,
            ['service', 'env', 'production', 'app1', 'TEST=123']
        )
        expected = 'No updates'
        assert expected in result.output

    # def test_service_deploy_the_same_tag(self, runner, mocker):
    #     mocked_exit = mocker.patch(
    #         'ecstools.lib.utils.deployment_completed')
    #     mocked_exit.side_effect = True
    #     result = runner.invoke(
    #         main.cli,
    #         ['service', 'deploy', 'production', 'app1', 'v0.1']
    #     )
    #     assert 'Elapsed:' in result.output
    #     assert 'production app1  0/1' in result.output

    # def test_service_deploy_the_same_tag_to_group(self, runner, mocker):
    #     mocked_exit = mocker.patch('ecstools.lib.utils.deployment_completed')
    #     mocked_exit.side_effect = True
    #     result = runner.invoke(
    #         main.cli,
    #         ['service', 'deploy', 'production', 'pytest-group', 'v0.1', '-g']
    #     )
    #     assert 'Elapsed:' in result.output
    #     assert 'production app1  0/1' in result.output
    #     assert 'production app2  0/1' in result.output

    def test_service_deploy_the_same_tag_to_bad_group(self, runner, mocker):
        result = runner.invoke(
            main.cli,
            ['service', 'deploy', 'production', 'bad-group', 'v0.1', '-g']
        )
        assert result.exit_code == 1
        expected = 'Error: Service group not in config file.\n'
        assert result.output == expected

    # TODO: Create moto ecr to validate the new tag
    # def test_service_deploy_new_tag(self, runner, mocker):
    #     mocked_exit = mocker.patch(
    #         'ecstools.lib.utils.deployment_completed')
    #     mocked_exit.side_effect = True
    #     result = runner.invoke(
    #         main.cli,
    #         ['service', 'deploy', 'production', 'app1', 'new_tag']
    #     )
    #     assert 'Elapsed:' in result.output
    #     assert 'production app1  0/1' in result.output

    def test_service_deploy_no_tags(self, runner):
        result = runner.invoke(
            main.cli,
            ['service', 'deploy', 'production', 'app1']
        )
        expected = 'Error: Specify one or more tags to be deployed.\n'
        assert result.exit_code == 1
        assert result.output == expected

    def test_service_desc(self, runner, mocker):
        mocked_net_config = mocker.patch(
            'ecstools.commands.service.desc.print_service_network_info')
        mocked_net_config.side_effect = None
        result = runner.invoke(main.cli, ['desc', 'production', 'app1'])
        assert 'production app1 production-app1:3' in result.output
        assert 'Desired: 1 Running: 0 Pending: 0' in result.output
        assert 'Container:        app1 @ app1:v0.1' in result.output

    # def test_service_scale(self, runner, mocker):
    #     mocked_exit = mocker.patch('ecstools.lib.utils.deployment_completed')
    #     mocked_exit.side_effect = True
    #     result = runner.invoke(
    #         main.cli,
    #         ['service', 'scale', 'production', 'app1', '1']
    #     )
    #     assert 'Elapsed:' in result.output
    #     assert 'production app1  0/1' in result.output

    # def test_service_top(self, runner, mocker):
    #     mocked_exit = mocker.patch('ecstools.lib.utils.deployment_completed')
    #     mocked_exit.side_effect = True
    #     result = runner.invoke(
    #         main.cli,
    #         ['service', 'top', 'production', 'app1', '-e']
    #     )
    #     assert 'Elapsed:' in result.output
    #     assert 'production app1  0/1' in result.output

    # def test_service_top_group(self, runner, mocker):
    #     mocked_exit = mocker.patch('ecstools.lib.utils.deployment_completed')
    #     mocked_exit.side_effect = True
    #     result = runner.invoke(
    #         main.cli,
    #         ['service', 'top', 'production', 'pytest-group', '-ge']
    #     )
    #     assert 'Elapsed:' in result.output
    #     assert 'production app1  0/1' in result.output
    #     assert 'production app2  0/1' in result.output

    def test_service_top_group_nonexistent(self, runner):
        result = runner.invoke(
            main.cli,
            ['service', 'top', 'production', 'nonexistent', '-ge']
        )
        assert result.exit_code == 1
        expected = 'Error: Service group not in config file.\n'
        assert result.output == expected

    # TODO: Fix
    # def test_service_top_group_bad_config(self, runner, mocker):
    #     mocked_local_config = mocker.patch('ecstools.lib.config.config')
    #     mocked_local_config.side_effect = []
    #     result = runner.invoke(
    #         main.cli,
    #         ['service', 'top', 'production', 'bad-config', '-ge']
    #     )
    #     assert result.exit_code == 1
    #     expected = 'Error: Section "service-group" not in config file.\n'
    #     assert result.output == expected
