import unittest
from sys import *
import os

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException

class QUnitTests(unittest.TestCase):
    driver = None
    waiter = None
    failed = False

    @classmethod
    def tearDownClass(cls):
        if not cls.failed:
            cls.driver.quit()

    @classmethod
    def setUpClass(cls):
        cls.driver = webdriver.Chrome()
        cls.waiter = WebDriverWait(cls.driver, 20)

    def get_el(self, selector):
        return QUnitTests.driver.find_element_by_css_selector(selector)

    def is_el_present(self, selector):
        try:
            QUnitTests.driver.find_element_by_css_selector(selector)
            return True
        except NoSuchElementException:
            return False
            
    def wait_for_el(self, selector):
        try:
            QUnitTests.waiter.until(lambda driver: self.is_el_present(selector))
        except TimeoutException:
            raise Exception('Never saw element %s' % (selector))
    
    def run_qunit(self, filename):
        QUnitTests.driver.get('file:///%s/tests/qunit/%s' % (os.getcwd(), filename))
        self.wait_for_el('#qunit-testresult')
        failed_el = self.get_el('#qunit-testresult .failed')
        if failed_el.text != '0':
            QUnitTests.failed = True
            raise Exception('Found failures in QUnit tests in %s' % filename) 

    def test_models(self):
        self.run_qunit('models_tests.html')

