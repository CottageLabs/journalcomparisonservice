from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver


class SeleniumTests(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        chromeOptions = Options()
        chromeOptions.add_argument('--no-sandbox')
        chromeOptions.add_argument("--headless=new")
        chromeOptions.add_argument('--disable-gpu')
        chromeOptions.add_argument('--disable-dev-shm-usage')
        chromeOptions.add_argument('--window-size=1920,1080')
        #chromeOptions.add_argument("--disable-notifications")
        cls.selenium = WebDriver(options=chromeOptions)
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_one_modal_element(self):
        '''
        Test that on the login page there is:
            - only one element of the class modal
            - that this is the feedback form
            - that it is not displayed
            - that it is displayed when the Contact us button is pressed
            - that it is removed when clicking outside the modal content
            - that when displayed it is removed when clicking the close modal button
        :return:
        '''
        self.selenium.get(self.live_server_url)
        modals = self.selenium.find_elements(By.CLASS_NAME, 'modal')
        self.assertEqual(len(modals), 1)
        self.assertEqual(modals[0].get_attribute('id'), 'feedback_form')

        feedback_modal = modals[0]
        # Modal does not display by default
        self.assertEqual(feedback_modal.get_attribute('style'), 'display: none;')

        # Modal displays when button clicked
        open_feedback_form = self.selenium.find_element(By.ID, 'open_feedback_form')
        open_feedback_form.click()
        self.assertEqual(feedback_modal.get_attribute('style'), 'display: block;')

        # Modal closes when clicked outside of modal content (200 pixels right of close button)
        close_feedback_form = self.selenium.find_element(By.ID, 'close_feedback_modal')
        ac = ActionChains(self.selenium)
        ac.move_to_element_with_offset(close_feedback_form, 200, 0).click().perform()
        self.assertEqual(feedback_modal.get_attribute('style'), 'display: none;')

        # Modal closes when close button clicked
        open_feedback_form.click()
        self.assertEqual(feedback_modal.get_attribute('style'), 'display: block;')
        close_feedback_form.click()
        self.assertEqual(feedback_modal.get_attribute('style'), 'display: none;')
