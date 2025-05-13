from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import dotenv_values
import os
import time
import mtranslate as mt

# Load environment variables
env_vars = dotenv_values(".env")
InputLanguage = env_vars.get("InputLanguage", "en-US")

# HTML code with language support
HtmlCode = '''<!DOCTYPE html>
<html lang="en">
<head>
    <title>Speech Recognition</title>
</head>
<body>
    <button id="start" onclick="startRecognition()">Start Recognition</button>
    <button id="end" onclick="stopRecognition()">Stop Recognition</button>
    <p id="output"></p>
    <script>
        const output = document.getElementById('output');
        let recognition;

        function startRecognition() {
            recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            recognition.lang = '';
            recognition.continuous = true;

            recognition.onresult = function(event) {
                const transcript = event.results[event.results.length - 1][0].transcript;
                output.textContent += transcript + " ";
            };

            recognition.start();
        }

        function stopRecognition() {
            if (recognition) {
                recognition.stop();
            }
        }
    </script>
</body>
</html>'''

HtmlCode = HtmlCode.replace("recognition.lang = '';", f"recognition.lang = '{InputLanguage}'")

# Save HTML
os.makedirs("Data", exist_ok=True)
with open(r"Data\Voice.html", "w", encoding="utf-8") as f:
    f.write(HtmlCode)

# Build path to file
current_dir = os.getcwd()
Link = os.path.join(current_dir, "Data", "Voice.html").replace("\\", "/")

# Chrome options
chrome_options = Options()
chrome_options.add_argument("--use-fake-ui-for-media-stream")
chrome_options.add_argument("--use-fake-device-for-media-stream")
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--disable-gpu")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# Set assistant status
TempDirPath = os.path.join(current_dir, "Frontend", "Files")
os.makedirs(TempDirPath, exist_ok=True)

def SetAssistantStatus(Status):
    with open(os.path.join(TempDirPath, "Status.data"), "w", encoding='utf-8') as file:
        file.write(Status)

# Capitalize and format user query
def QueryModifier(Query):
    new_query = Query.lower().strip()
    if not new_query:
        return ""

    if not new_query.endswith("?") and any(qw in new_query for qw in ["how", "what", "why", "can", "when", "where"]):
        new_query += "?"
    elif not new_query.endswith((".", "!", "?")):
        new_query += "."

    return new_query.capitalize()

# Translate non-English to English
def UniversalTranslator(Text):
    english_translation = mt.translate(Text, "en", "auto")
    return english_translation.capitalize()

# Speech Recognition
def SpeechRecognition():
    driver.get("file:///" + Link)
    driver.find_element(By.ID, "start").click()

    output_text = ""
    timeout = 15  # Max wait time

    for _ in range(timeout):
        try:
            output_element = driver.find_element(By.ID, "output")
            output_text = output_element.text.strip()

            if output_text:
                driver.find_element(By.ID, "end").click()
                break
        except Exception:
            pass
        time.sleep(1)

    if not output_text:
        return "Could not recognize any speech."

    if "en" in InputLanguage.lower():
        return QueryModifier(output_text)
    else:
        SetAssistantStatus("Translating...")
        return QueryModifier(UniversalTranslator(output_text))

# Run
if __name__ == "__main__":
    while True:
        result = SpeechRecognition()
        print("Recognized:", result)
