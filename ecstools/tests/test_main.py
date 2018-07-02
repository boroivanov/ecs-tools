import ecstools.main as main

version = '0.1.3'


class TestMain(object):
    def test_version(self, runner):
        result = runner.invoke(main.cli, ['--version'])
        assert result.exit_code == 0
        assert version in result.output

    def test_subcommands_listing(self, runner):
        result = runner.invoke(main.cli)
        assert result.exit_code == 0
        subcommands = ['cluster', 'service', 'task-definition']
        assert all(x in result.output for x in subcommands)
