#!/usr/bin/env python3
"""Propose a first set of ADDITIONAL COMPANIES (not in the Excel) for review.

All are added with status 'pending_review': they appear in the Companies page
under "Awaiting review" and are NOT monitored until you approve them with
    python scripts/manage_companies.py approve "<name>"
Career portals are left empty on purpose: after approval, the discovery step
reads the official website and records the portal it actually finds.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fcip.companies import add_additional_company, load_companies  # noqa: E402
from fcip.sources import sync_sources  # noqa: E402
from fcip.util import load_settings  # noqa: E402

NOTE = " Website entered from general knowledge and not yet fetched: confirm it when you review."
SEED = [
    ("Capvis", "PE", "Switzerland", "Zug", "https://www.capvis.com", "", "Swiss mid-market buy-out fund based in Baar (canton Zug)." + NOTE),
    ("Ufenau Capital Partners", "PE", "Switzerland", "Pfaeffikon", "https://www.ufenau.com", "", "Swiss private-equity firm (service-sector buy-and-build) in Pfaeffikon SZ, near Zurich and Zug." + NOTE),
    ("LGT Capital Partners", "Asset Manager", "Switzerland", "Pfaeffikon", "https://www.lgtcp.com", "", "Alternative-investment manager (private equity, hedge funds) in Pfaeffikon SZ; the Excel only lists LGT Bank." + NOTE),
    ("Unigestion", "Asset Manager", "Switzerland", "Geneva", "https://www.unigestion.com", "", "Geneva asset manager with private-equity and equities teams." + NOTE),
    ("Bellevue Asset Management", "Asset Manager", "Switzerland", "Zurich", "https://www.bellevue.ch", "", "Specialist asset manager (healthcare equities, private markets) in the Zurich area." + NOTE),
    ("Swiss Life Asset Managers", "Asset Manager", "Switzerland", "Zurich", "https://www.swisslife-am.com", "", "Large Zurich asset manager (real assets, fixed income, equities)." + NOTE),
    ("Leonteq", "Altro", "Switzerland", "Zurich", "https://www.leonteq.com", "", "Zurich structured-products and derivatives house: relevant for quantitative and structuring roles." + NOTE),
    ("Sygnum Bank", "Banca privata", "Switzerland", "Zurich", "https://www.sygnum.com", "", "Zurich digital-asset bank with asset-management and research teams." + NOTE),
    ("Zürcher Kantonalbank", "Altro", "Switzerland", "Zurich", "https://www.zkb.ch", "", "Zurich cantonal bank with asset management (Swisscanto), research and corporate-finance units." + NOTE),
    ("Kepler Cheuvreux", "Boutique IB", "Italy", "Milan", "https://www.keplercheuvreux.com", "", "European equity research, ECM and corporate-finance house with offices in Milan, Zurich and Geneva." + NOTE),
    ("UniCredit", "Bulge Bracket", "Italy", "Milan", "https://www.unicreditgroup.eu", "https://www.unicreditgroup.eu/en/careers.html", "Milan CIB and advisory franchise; the Excel lists only its subsidiary Cordusio SIM (career page taken from that Excel row)."),
    ("Intesa Sanpaolo IMI Corporate & Investment Banking", "Bulge Bracket", "Italy", "Milan", "https://group.intesasanpaolo.com", "https://group.intesasanpaolo.com/it/careers", "Milan investment-banking arm of Intesa Sanpaolo; the Excel lists only group subsidiaries (career page taken from the Fideuram row)."),
]


def main() -> int:
    settings = load_settings()
    added = [name for name, *rest in SEED if add_additional_company(name, *rest, settings, "pending_review", "initial research")]
    sync_sources(load_companies()["companies"])
    print(f"{len(added)} additional compan(ies) proposed for review: {', '.join(added) or 'none (already present)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
