from playwright.sync_api import sync_playwright
print('gg')
p = sync_playwright().start()
browser = p.chromium.launch(headless=True)
page = browser.new_page(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36')
page.goto("http://playwright.dev")
print(page.title())
browser.close()
