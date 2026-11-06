"""Read the public Mailchimp campaign archive and write latest.json.

Runs in GitHub Actions. No API key: it reads the same public archive page
anyone can open, so it sees every campaign that was sent as a campaign.
Send test emails with Mailchimp's "Send a test email" (not as a campaign
to a small segment) so they never reach the archive or this page.
"""
import html, json, os, re, sys, urllib.request

ARCHIVE = os.environ.get(
    "ARCHIVE_URL",
    "https://us4.campaign-archive.com/home/?u=d73891da54d38f9eae371cd4d&id=cc8d3c37f6")
OUT = os.environ.get("OUT_FILE", "latest.json")
KEEP = 10
PREFIX = re.compile(r"^\s*(ApplyAI\s+)?(AI\s+)?Pulse\s*[:\-–·]\s*", re.I)
# One archive row:  11/06/2026 - <a href="http://eepurl.com/xxx" title="Subject" ...>Subject</a>
ROW = re.compile(r'(\d{1,2})/(\d{1,2})/(\d{4})\s*-\s*<a\s+href="([^"]+)"[^>]*?title="([^"]*)"', re.I)

req = urllib.request.Request(ARCHIVE, headers={"User-Agent": "applyai-pulse-latest/1.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    page = r.read().decode("utf-8", "replace")

editions = []
for m, d, y, link, subject in ROW.findall(page):   # archive lists newest first, dates are mm/dd/yyyy
    subject = html.unescape(subject).strip()
    link = html.unescape(link).strip().replace("http://", "https://", 1)
    if not subject or not link.startswith("https://"):
        continue
    editions.append({
        "title": PREFIX.sub("", subject).strip(),
        "subject": subject,
        "sent": f"{y}-{int(m):02d}-{int(d):02d}",
        "url": link,
    })
    if len(editions) >= KEEP:
        break

if not editions:
    sys.exit("Couldn't read any editions from the archive; leaving latest.json as it is.")

new = json.dumps({"latest": editions[0], "editions": editions}, ensure_ascii=False, indent=2) + "\n"
try:
    old = open(OUT, encoding="utf-8").read()
except FileNotFoundError:
    old = ""
if new != old:
    open(OUT, "w", encoding="utf-8").write(new)
    print("Updated:", editions[0]["title"], editions[0]["sent"])
else:
    print("No change.")
