from html import escape
from html.parser import HTMLParser
from urllib.parse import urlparse

ALLOWED_TAGS = {
    "article", "aside", "blockquote", "br", "code", "div", "em", "figcaption",
    "figure", "footer", "h1", "h2", "h3", "header", "hr", "li", "main", "ol",
    "p", "pre", "section", "small", "span", "strong", "ul",
}
VOID_TAGS = {"br", "hr"}
ALLOWED_ATTRIBUTES = {"class", "aria-label", "role"}
BLOCKED_CONTENT_TAGS = {"script", "style", "iframe", "object", "embed", "svg", "math"}


class SafeHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.output: list[str] = []
        self.open_tags: list[str] = []
        self.blocked_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in BLOCKED_CONTENT_TAGS:
            self.blocked_depth += 1
            return
        if self.blocked_depth:
            return
        if tag not in ALLOWED_TAGS:
            return
        safe_attrs = []
        for name, value in attrs:
            name = name.lower()
            if name in ALLOWED_ATTRIBUTES and value is not None:
                safe_attrs.append(f' {name}="{escape(value, quote=True)}"')
        self.output.append(f"<{tag}{''.join(safe_attrs)}>")
        if tag not in VOID_TAGS:
            self.open_tags.append(tag)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in BLOCKED_CONTENT_TAGS and self.blocked_depth:
            self.blocked_depth -= 1
            return
        if self.blocked_depth:
            return
        if tag in self.open_tags:
            while self.open_tags:
                current = self.open_tags.pop()
                self.output.append(f"</{current}>")
                if current == tag:
                    break

    def handle_data(self, data: str) -> None:
        if not self.blocked_depth:
            self.output.append(escape(data))

    def handle_entityref(self, name: str) -> None:
        self.output.append(f"&amp;{escape(name)};")

    def handle_charref(self, name: str) -> None:
        self.output.append(f"&amp;#{escape(name)};")

    def result(self) -> str:
        while self.open_tags:
            self.output.append(f"</{self.open_tags.pop()}>")
        return "".join(self.output)


def sanitize_html(content: str) -> str:
    parser = SafeHTMLParser()
    parser.feed(content)
    parser.close()
    return parser.result()


def is_safe_external_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)
