import os, re, sys, hashlib, urllib.request
from html.parser import HTMLParser

class T(HTMLParser):
    def __init__(self):
        super().__init__()
        self.out, self.skip = [], 0
    def handle_starttag(self, tag, a):
        if tag in ("script", "style", "noscript", "svg"):
            self.skip += 1
        if tag in ("p", "br", "div", "li", "tr", "h1", "h2", "h3", "h4", "pre"):
            self.out.append("\n")
        if tag == "a" and dict(a).get("href"):
            self.href = dict(a)["href"]
    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript", "svg") and self.skip:
            self.skip -= 1
    def handle_data(self, d):
        if not self.skip:
            self.out.append(d)

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (url2text)"})
    with urllib.request.urlopen(req, timeout=40) as r:
        raw = r.read(3_000_000)
        ctype = r.headers.get("Content-Type", "")
        enc = r.headers.get_content_charset() or "utf-8"
    text = raw.decode(enc, "replace")
    if "html" in ctype.lower() or text.lstrip()[:15].lower().startswith(("<!doctype", "<html")):
        p = T()
        p.feed(text)
        text = "".join(p.out)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n+", "\n\n", text).strip()
    return text

urls = [u.strip() for u in os.environ.get("URLS", "").splitlines() if u.strip().startswith("http")]
if not urls and os.path.exists("urls.txt"):
    urls = [u.strip() for u in open("urls.txt") if u.strip().startswith("http")]
os.makedirs("out", exist_ok=True)
index = open("out/index.txt").read() if os.path.exists("out/index.txt") else ""
for u in urls:
    name = hashlib.sha1(u.encode()).hexdigest()[:12] + ".txt"
    try:
        body = get(u)[:400000]
    except Exception as e:
        body = "FETCH ERROR: %s" % e
    doc = "SOURCE: %s\n\n%s\n" % (u, body)
    open("out/" + name, "w").write(doc)
    open("out/latest.txt", "w").write(doc)
    if name not in index:
        index += "%s %s\n" % (name, u)
    print("fetched", u, len(body))
open("out/index.txt", "w").write(index)
