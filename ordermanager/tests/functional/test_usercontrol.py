from ordermanager.tests import *

class TestUsercontrolController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='usercontrol', action='index'))
        # Test response...
