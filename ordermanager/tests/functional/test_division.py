from ordermanager.tests import *

class TestDivisionController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='division', action='index'))
        # Test response...
