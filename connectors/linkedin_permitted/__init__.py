"""LinkedIn: permitted use only.

LinkedIn's User Agreement prohibits automated scraping, and its job data is
not offered through a public API. This module therefore performs NO automated
requests to linkedin.com. It provides two things that stay within the rules:

1. search_url(): a ready-made public LinkedIn Jobs search link per company
   and location, which you open yourself in your own browser session.
2. Manual capture: a posting you found on LinkedIn can be added with
   scripts/add_manual_job.py; it is stored with verification 'LINKEDIN ONLY'
   until the same role is seen on the employer's own portal, at which point
   the records are merged and upgraded to 'VERIFIED OFFICIAL'.
"""
from urllib.parse import quote_plus

NAME = "linkedin"
AUTOMATED = False
LIMITATION = ("LinkedIn is not polled automatically: its terms forbid scraping and there is no public jobs API. "
              "Coverage comes from employer portals; LinkedIn is available as one-click search links and manual capture.")

# f_E=1 internship, 2 entry level; f_TPR=r604800 posted in the last 7 days
def search_url(company: str, location: str | None = None, recent_days: int = 7) -> str:
    q = f"https://www.linkedin.com/jobs/search/?keywords={quote_plus(company)}&f_E=1%2C2&f_TPR=r{recent_days * 86400}&sortBy=DD"
    if location:
        q += f"&location={quote_plus(location)}"
    return q
