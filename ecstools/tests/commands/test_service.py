import ecstools.main as main


class TestService(object):
    def test_service_subcommand(self, runner):
        result = runner.invoke(main.cli, ['service'])
        assert result.exit_code == 0

    def test_service_ls(self, runner):
        result = runner.invoke(main.cli, ['service', 'ls', 'production'])
        expected = 'app1\napp2\nworker1\n'
        assert result.output == expected

    def test_service_env(self, runner):
        result = runner.invoke(
            main.cli,
            ['service', 'env', 'production', 'app1']
        )
        expected = 'Current task definition for production app1: ' + \
            'production-app1:3\n\n==> Container: app1\nTEST=123\n'
        assert result.output == expected
