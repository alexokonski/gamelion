from gamelion.tests import *

class TestServersController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='servers', action='index'))
        # Test response...
