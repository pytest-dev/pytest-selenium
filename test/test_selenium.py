from webserver import SimpleWebServer

def setup_module(module):
    webserver = SimpleWebServer()
    webserver.start()
    TestSeleniumOneAndTwo.webserver = webserver


class TestSeleniumOneAndTwo:

    def testShouldLoadSeleniumOne(self, mozwebqa):
        mozwebqa.selenium.open(mozwebqa.base_url + ":%d/index.html" % self.webserver.port)

    def testShouldLoadSeleniumTwo(self, mozwebqa):
        mozwebqa.selenium.get(mozwebqa.base_url + ":%d/index.html" % self.webserver.port)

def teardown_module(module):
    TestSeleniumOneAndTwo.webserver.stop()
