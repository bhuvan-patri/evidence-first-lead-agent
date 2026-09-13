from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


class BrowserCollector:
    def __init__(
        self,
        headless: bool = True,
        timeout: int = 30000,
    ):
        self.headless = headless
        self.timeout = timeout

    def fetch_page(self, url: str) -> dict:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.headless
            )

            try:
                page = browser.new_page()
                page.set_default_timeout(
                    self.timeout
                )

                try:
                    response = page.goto(
                        url,
                        wait_until="domcontentloaded",
                        timeout=self.timeout,
                    )

                    page.wait_for_timeout(1500)

                    return {
                        "url": page.url,
                        "status_code": (
                            response.status
                            if response
                            else None
                        ),
                        "title": page.title(),
                        "text": page.locator(
                            "body"
                        ).inner_text(),
                        "sections": self._extract_sections(
                            page
                        ),
                        "success": True,
                        "error": None,
                    }

                except PlaywrightTimeoutError:
                    return {
                        "url": url,
                        "status_code": None,
                        "title": "",
                        "text": "",
                        "sections": [],
                        "success": False,
                        "error": "Page navigation timed out",
                    }

                except Exception as exc:
                    return {
                        "url": url,
                        "status_code": None,
                        "title": "",
                        "text": "",
                        "sections": [],
                        "success": False,
                        "error": (
                            f"{type(exc).__name__}: {exc}"
                        ),
                    }

            finally:
                browser.close()

    def _extract_sections(self, page) -> list[dict]:
        """
        Extract meaningful page sections while preserving
        heading/content relationships.

        A section starts at a heading and contains the visible
        text belonging to that heading until the next heading.
        """

        return page.locator(
            "body"
        ).evaluate(
            """
            (body) => {
                const headingSelector =
                    "h1, h2, h3, h4, h5, h6";

                const headings = Array.from(
                    body.querySelectorAll(headingSelector)
                );

                const sections = [];

                for (let i = 0; i < headings.length; i++) {
                    const heading = headings[i];

                    const level = Number(
                        heading.tagName.substring(1)
                    );

                    const title =
                        (heading.innerText || "")
                            .replace(/\\s+/g, " ")
                            .trim();

                    if (!title) {
                        continue;
                    }

                    const contentParts = [];

                    let current =
                        heading.nextElementSibling;

                    while (current) {
                        if (
                            /^H[1-6]$/.test(
                                current.tagName
                            )
                        ) {
                            break;
                        }

                        const text =
                            (current.innerText || "")
                                .replace(/\\s+/g, " ")
                                .trim();

                        if (text) {
                            contentParts.push(text);
                        }

                        current =
                            current.nextElementSibling;
                    }

                    sections.push({
                        heading: title,
                        level: level,
                        content: contentParts.join(
                            "\\n"
                        ),
                    });
                }

                return sections;
            }
            """
        )