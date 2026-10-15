"""Display helpers and notebook styling."""

from __future__ import annotations

import html
import warnings

import pandas as pd

try:
    from IPython.display import HTML, Image, Markdown, display

    IPYTHON_AVAILABLE = True
except Exception:
    IPYTHON_AVAILABLE = False

    class _DisplayText:
        def __init__(self, data: str = "", **_kwargs: object) -> None:
            self.data = data

        def __repr__(self) -> str:
            return str(self.data)

    HTML = Markdown = _DisplayText

    def Image(filename: str | None = None, width: int | None = None, **_kwargs: object) -> str:
        return f"[image: {filename}, width={width}]"

    def display(obj: object | None = None) -> None:
        if hasattr(obj, "to_string"):
            try:
                print(obj.to_string(index=False))
                return
            except TypeError:
                print(obj.to_string())
                return
        print(obj)


THESIS_CSS = """
<style>
:root {
  --thesis-ink: #1f2933;
  --thesis-muted: #52616b;
  --thesis-border: #d6dde3;
  --thesis-bg: #ffffff;
  --thesis-soft: #f6f8fa;
  --thesis-accent: #0f766e;
}
.jp-RenderedHTMLCommon, .rendered_html {
  color: var(--thesis-ink);
  line-height: 1.55;
}
.jp-RenderedHTMLCommon h1, .rendered_html h1 {
  margin-top: 0.4em;
  padding-bottom: 0.25em;
  border-bottom: 1px solid var(--thesis-border);
}
.jp-RenderedHTMLCommon h2, .rendered_html h2 {
  margin-top: 1.9em;
  padding-top: 0.2em;
  border-top: 1px solid var(--thesis-border);
}
.jp-RenderedHTMLCommon h3, .rendered_html h3 {
  margin-top: 1.25em;
}
.thesis-box {
  border: 1px solid var(--box-border);
  background: var(--box-bg);
  color: var(--box-fg);
  padding: 10px 13px;
  border-radius: 6px;
  margin: 12px 0 16px 0;
}
.thesis-box strong {
  display: block;
  margin-bottom: 4px;
}
.thesis-table-wrap {
  max-width: 100%;
  overflow-x: auto;
  margin: 8px 0 14px 0;
  border: 1px solid var(--thesis-border);
  border-radius: 6px;
  background: var(--thesis-bg);
}
.thesis-table {
  border-collapse: collapse;
  width: 100%;
  min-width: 620px;
  font-size: 12.8px;
}
.thesis-table th {
  background: var(--thesis-soft);
  border-bottom: 1px solid var(--thesis-border);
  color: var(--thesis-ink);
  font-weight: 600;
  text-align: center;
  padding: 7px 8px;
  vertical-align: top;
}
.thesis-table td {
  border-top: 1px solid #edf1f4;
  padding: 6px 8px;
  vertical-align: top;
  max-width: 300px;
  overflow-wrap: anywhere;
}
.thesis-note {
  color: var(--thesis-muted);
  font-size: 12.5px;
  margin: 4px 0 8px 0;
}
.thesis-figure-note {
  padding: 3px 0 18px 0;
  margin: 6px 0 18px 0;
  color: var(--thesis-ink);
  font-size: 13px;
}
.thesis-figure-note code,
.thesis-note code {
  white-space: normal;
}
</style>
"""


def configure_notebook() -> None:
    pd.set_option("display.max_rows", 20)
    pd.set_option("display.max_columns", 80)
    pd.set_option("display.width", 180)
    pd.set_option("display.float_format", lambda x: f"{x:,.4f}")
    warnings.filterwarnings("ignore", category=FutureWarning)
    display(HTML(THESIS_CSS))


def html_box(title: str, body: str, tone: str = "finding") -> None:
    colors = {
        "finding": ("#0f3d3e", "#edf7f6", "#9cc8c6"),
        "caution": ("#4a3b16", "#fff8e8", "#e5c873"),
        "context": ("#263238", "#f4f7f9", "#cbd5dc"),
    }
    fg, bg, border = colors.get(tone, colors["finding"])
    display(
        HTML(
            "<div class='thesis-box' "
            f"style='--box-border:{border}; --box-bg:{bg}; --box-fg:{fg};'>"
            f"<strong>{html.escape(title)}</strong>{html.escape(body)}</div>"
        )
    )


def key_finding(body: str) -> None:
    html_box("Thesis Reading", body, "finding")


def caution_box(body: str) -> None:
    html_box("Interpretive Scope", body, "caution")


def audit_box(title: str, body: str) -> None:
    html_box(title, body, "context")
