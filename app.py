from selenium import webdriver
from flask import Flask
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

app = Flask(__name__)

@app.route('/')
def hello_world():
    print('Hello from Flask!')
    print("working")

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=chrome_options)

    try:

        driver.get("https://web.whatsapp.com/")
        print("Please scan the QR code with your phone.")


        # time.sleep(20)


        search_box_locator = (By.XPATH, '//div[@contenteditable="true" and @data-tab="3"]')
        WebDriverWait(driver, 60).until(EC.presence_of_element_located(search_box_locator))
        print("located chat box")


        contact_number = '8882084910'
        search_box = driver.find_element(*search_box_locator)
        search_box.send_keys(contact_number)
        search_box.send_keys(Keys.ENTER)


        input_box_locator = (By.XPATH, '/html/body/div[1]/div/div/div[5]/div/footer/div[1]/div/span[2]/div/div[2]/div[1]/div[2]/div/p')
        WebDriverWait(driver, 30).until(EC.presence_of_element_located(input_box_locator))


        message_box = driver.find_element(*input_box_locator)



        ActionChains(driver).move_to_element(message_box).click().send_keys("using pythonanywhee").send_keys(Keys.ENTER).perform()


        print("Message sent successfully!")

    finally:

        driver.quit()
    return 'hello'

if __name__ == '__main__':
    app.run(debug=True)
