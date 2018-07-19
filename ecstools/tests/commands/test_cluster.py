import ecstools.main as main


class TestCluster(object):
    def test_cluster_subcommand(self, runner):
        result = runner.invoke(main.cli, ['cluster'])
        assert result.exit_code == 0

    def test_cluster_ls(self, runner):
        result = runner.invoke(main.cli, ['cluster', 'ls'])
        expected = 'development\nproduction\nstaging\n'
        assert result.output == expected

    def test_cluster_ls_alias(self, runner):
        result = runner.invoke(main.cli, ['cls'])
        expected = 'development\nproduction\nstaging\n'
        assert result.output == expected
