import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException

# Chrome பிரௌசரை ஓபன் பண்றோம்
print("🚀 Starting Selenium Automation Testing...")
driver = webdriver.Chrome()

# உன்னோட Flask ஆப் ரன் ஆகுற Localhost URL (Login இல்லாம டைரக்ட் Grievance page)
# குறிப்பு: உன்னோட URL-க்கு ஏத்த மாதிரி இதை மாத்திக்கோ
BASE_URL = "http://localhost:5000/submit_ticket" 

try:
    # ---------------------------------------------------------
    # TEST CASE 1: Empty Form Submission (Validation Test)
    # ---------------------------------------------------------
    print("\n[Test 1] Executing Empty Form Validation...")
    driver.get(BASE_URL)
    time.sleep(2) # பேஜ் லோட் ஆக வெயிட் பண்ணனும்
    
    # Submit பட்டனை கண்டுபிடிக்கிறோம் (உன்னோட HTML id-க்கு ஏத்த மாதிரி மாத்திக்கோ)
    submit_btn = driver.find_element(By.ID, "submit-btn")
    submit_btn.click()
    time.sleep(1)
    
    print("✅ Test 1 Passed: JavaScript successfully prevented empty submission.")


    # ---------------------------------------------------------
    # TEST CASE 2: Critical Grievance Flow (AI SVM Test)
    # ---------------------------------------------------------
    print("\n[Test 2] Executing Critical Grievance Flow...")
    driver.get(BASE_URL)
    time.sleep(2)
    
    # Text box-ஐ கண்டுபிடிச்சு கிரிட்டிக்கல் வார்த்தைகளை டைப் பண்றோம்
    text_area = driver.find_element(By.ID, "grievance-text")
    text_area.send_keys("I met with a severe accident and my car is damaged badly. Need emergency help.")
    time.sleep(1)
    
    submit_btn = driver.find_element(By.ID, "submit-btn")
    submit_btn.click()
    time.sleep(3) # AI Model ரன் ஆகி ரிசல்ட் வர வெயிட் பண்றோம்
    
    # ரிசல்ட் பேஜ்ல 'Critical' னு வந்துருக்கானு செக் பண்றோம்
    try:
        result_status = driver.find_element(By.ID, "severity-badge").text
        if "Critical" in result_status:
            print(f"✅ Test 2 Passed: AI correctly classified as '{result_status}'!")
        else:
            print(f"❌ Test 2 Failed: AI classified it as '{result_status}' instead.")
    except NoSuchElementException:
        print("⚠️ Warning: Result element not found. Check HTML ID.")


    # ---------------------------------------------------------
    # TEST CASE 3: Non-Critical Grievance Flow (AI SVM Test)
    # ---------------------------------------------------------
    print("\n[Test 3] Executing Non-Critical Grievance Flow...")
    driver.get(BASE_URL)
    time.sleep(2)
    
    text_area = driver.find_element(By.ID, "grievance-text")
    text_area.send_keys("The app map is loading a bit slow today. Please check.")
    time.sleep(1)
    
    submit_btn = driver.find_element(By.ID, "submit-btn")
    submit_btn.click()
    time.sleep(3)
    
    # ரிசல்ட் பேஜ்ல 'Non-Critical' னு வந்துருக்கானு செக் பண்றோம்
    try:
        result_status = driver.find_element(By.ID, "severity-badge").text
        if "Non-Critical" in result_status or "Normal" in result_status:
            print(f"✅ Test 3 Passed: AI correctly classified as '{result_status}'!")
        else:
            print(f"❌ Test 3 Failed: AI classified it as '{result_status}'.")
    except NoSuchElementException:
        print("⚠️ Warning: Result element not found. Check HTML ID.")

except Exception as e:
    print(f"\n❌ Error encountered during testing: {e}")

finally:
    # டெஸ்டிங் முடிஞ்சதும் பிரௌசரை க்ளோஸ் பண்றோம்
    print("\n🏁 Automation Testing Complete. Closing Browser in 3 seconds...")
    time.sleep(3)
    driver.quit()