import ecstools.lib.utils as utils


class TestUtils(object):
    def test_index(self):
        result = utils.index()
        assert result == 1
        result = utils.index()
        assert result == 2
