import ecstools.main as main

version = '0.2.6'


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

    def test_missing_profile(self, runner):
        result = runner.invoke(
            main.cli,
            ['--profile', 'no-profile', 'cluster']
        )
        assert result.exit_code == 1
        expected = 'The config profile (no-profile) could not be found\n'
        assert result.output == expected

    def test_missing_region(self, runner):
        """
        Requires `[profile no-region]` in ~/.aws/config for local tests.
        """
        result = runner.invoke(
            main.cli,
            ['--profile', 'no-region', 'cluster']
        )
        assert result.exit_code == 1
        expected = 'You must specify a region.\n'
        assert result.output == expected
