from playwright.sync_api import Browser, Page, sync_playwright


CDP_URL = "http://127.0.0.1:9222"


class GoogleFormBrowser:
    def __init__(self, cdp_url: str = CDP_URL):
        self.cdp_url = cdp_url
        self.playwright = None
        self.browser: Browser | None = None
        self.page: Page | None = None

    def connect(self) -> None:
        self.playwright = sync_playwright().start()

        self.browser = self.playwright.chromium.connect_over_cdp(
            self.cdp_url
        )

        for context in self.browser.contexts:
            for page in context.pages:
                if "docs.google.com/forms" in page.url:
                    self.page = page
                    break

            if self.page:
                break

        if self.page is None:
            raise RuntimeError("No Google Form page found.")

        print("Connected to:", self.page.url)

    def get_questions(self) -> list[dict]:
        if self.page is None:
            raise RuntimeError("Browser is not connected.")

        question_blocks = self.page.locator('[role="listitem"]')

        questions = []

        for i in range(question_blocks.count()):
            block = question_blocks.nth(i)

            if not block.is_visible():
                continue

            radios = block.get_by_role("radio")

            if radios.count() == 0:
                continue

            text = block.inner_text().strip()
            lines = [line.strip() for line in text.splitlines() if line.strip()]

            if not lines:
                continue

            question_text = lines[0]

            options = []

            for j in range(radios.count()):
                radio = radios.nth(j)
                option_text = (
                    radio.get_attribute("aria-label")
                    or radio.inner_text().strip()
                )

                options.append({
                    "index": j,
                    "identifier": option_text,
                    "text": option_text,
                })

            questions.append({
                "question": question_text,
                "options": options,
            })

        return questions

    def select_option(self, question_index: int, option_index: int) -> None:
        if self.page is None:
            raise RuntimeError("Browser is not connected.")

        question_blocks = self.page.locator('[role="listitem"]')

        visible_questions = []

        for i in range(question_blocks.count()):
            block = question_blocks.nth(i)

            if not block.is_visible():
                continue

            if block.get_by_role("radio").count() == 0:
                continue

            visible_questions.append(block)

        if not 0 <= question_index < len(visible_questions):
            raise IndexError("Question index out of range.")

        question = visible_questions[question_index]
        radios = question.get_by_role("radio")

        if not 0 <= option_index < radios.count():
            raise IndexError("Option index out of range.")

        radios.nth(option_index).click()

    def click_next(self) -> bool:
        if self.page is None:
            raise RuntimeError("Browser is not connected.")

        next_button = self.page.get_by_role(
            "button", name="Next", exact=True
        )
        if next_button.count() == 0 or not next_button.is_visible():
            return False

        next_button.click()
        return True

    def submit(self) -> None:
        if self.page is None:
            raise RuntimeError("Browser is not connected.")

        self.page.get_by_role("button", name="Submit").click()

    def close(self) -> None:
        if self.playwright:
            self.playwright.stop()