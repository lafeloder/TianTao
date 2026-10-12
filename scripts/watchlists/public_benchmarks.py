"""Public vacancy benchmark collector for a scheduled tracker.

Dependencies: Python >=3.10 and lxml. No login, token, search API or paid data.
All parse/screen functions are pure. collect_public_benchmarks injects a GET
transport and can be exercised against cached HTML in regression checks.
Returned descriptions are transient research inputs; a publisher should keep
only factual fields, a short own summary and provenance, not full ad text.
"""
from __future__ import annotations
import concurrent.futures
import datetime as dt
import json
import re
import urllib.request
from typing import Callable
from lxml import html

OPENPOSTDOC = "https://www.openpostdoc.org/board"
EJM = "https://econjobmarket.org"
EUROPE_COUNTRIES = {
    "Albania", "Andorra", "Austria", "Belarus", "Belgium", "Bosnia and Herzegovina",
    "Bulgaria", "Croatia", "Cyprus", "Czech Republic", "Czechia", "Denmark", "Estonia",
    "Finland", "France", "Germany", "Greece", "Hungary", "Iceland", "Ireland", "Italy",
    "Kosovo", "Latvia", "Liechtenstein", "Lithuania", "Luxembourg", "Malta", "Moldova",
    "Monaco", "Montenegro", "Netherlands", "North Macedonia", "Norway", "Poland",
    "Portugal", "Romania", "San Marino", "Serbia", "Slovakia", "Slovenia", "Spain",
    "Sweden", "Switzerland", "Ukraine", "United Kingdom", "Vatican City",
}


def get_public_html(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "AcademicVacancyTracker/1.0 (+public-page research)"})
    with urllib.request.urlopen(request, timeout=35) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_openpostdoc_html(document: str) -> dict:
    """Decode observed public Next.js RSC hydration props, independent of JS execution."""
    chunks = []
    for match in re.findall(r"self\.__next_f\.push\((.*?)\)</script>", document, re.S):
        decoded = json.loads(match)
        if isinstance(decoded, list) and len(decoded) > 1 and isinstance(decoded[1], str):
            chunks.append(decoded[1])
    payload = "".join(chunks)
    marker = '"positions":'
    offset = payload.find(marker)
    if offset < 0:
        raise ValueError("OpenPostdoc public hydration contains no positions prop")
    positions, consumed = json.JSONDecoder().raw_decode(payload[offset + len(marker):])
    tail = payload[offset + len(marker) + consumed:]
    metadata = {key: int(value) for key, value in re.findall(r'"(total|otherCount|page|pageCount|pageSize)":([0-9]+)', tail)}
    if not isinstance(positions, list) or not all(key in metadata for key in ("total", "pageCount", "page")):
        raise ValueError("OpenPostdoc incomplete hydration props")
    return {"positions": positions, "metadata": metadata}


def parse_date(value: str | None) -> str | None:
    if not value:
        return None
    for format_string in ("%Y-%m-%d", "%d %b %Y", "%d %B %Y"):
        try:
            return dt.datetime.strptime(value.strip(), format_string).date().isoformat()
        except ValueError:
            pass
    return None


def parse_ejm_html(document: str, page_url: str) -> dict:
    """Parse every public EJM card once, including nested featured advertisements."""
    doc = html.fromstring(document)
    records = []
    for anchor in doc.xpath('//a[starts-with(@id,"title-")]'):
        card = anchor.xpath('ancestor::div[contains(concat(" ", normalize-space(@class), " "), " card ")][1]')[0]
        raw_id = anchor.get("id").split("-")[-1]
        rows = card.xpath('./div[@class="row"]')
        columns = rows[0].xpath('./div') if rows else []
        header = [" ".join(column.text_content().split()) for column in columns[:4]]
        text = "\n".join(line.strip() for line in card.text_content().splitlines() if line.strip())
        record = {
            "id": raw_id, "title": " ".join(anchor.text_content().split()),
            "sourceUrl": f"{EJM}/positions/{raw_id}", "statusSourceUrl": f"{page_url}#position{raw_id}",
            "headerColumns": header, "advertiser": header[1] if len(header) > 1 else None,
            "positionTypesAndFields": header[2] if len(header) > 2 else None,
            "text": text, "links": list(dict.fromkeys(card.xpath('.//a/@href'))),
        }
        for strong in card.xpath('.//strong'):
            label = " ".join(strong.text_content().split()).rstrip(":")
            if label in {"Location of job", "Degree required", "Job start date", "Job duration", "Salary",
                         "Application deadline", "Letters of reference required", "Target date for applications",
                         "Current search status", "Posting end date"}:
                value = " ".join(strong.getparent().text_content().split())
                record[label] = value[len(label) + 1:].strip() if value.startswith(label + ":") else value
        if len(columns) > 3:
            dated = columns[3].xpath('./span')
            record["postedDate"] = parse_date(next((x.text_content() for x in dated if "bg-info" in (x.get("class") or "")), None))
            record["targetDate"] = parse_date(next((x.text_content() for x in dated if "positive" in (x.get("class") or "")), None))
            record["deadline"] = parse_date(next((x.text_content() for x in dated if "negative" in (x.get("class") or "")), None))
            # Only the grey final span is display closure. Do not confuse it with the deadline.
            record["postingEnd"] = parse_date(next((x.text_content() for x in dated if "#cccccc" in (x.get("style") or "")), None))
        states = ["Accepting applications", "Reviewing applications", "Scheduling interviews", "Arranging flyouts",
                  "Making offers", "Position filled", "Search cancelled", "Search completed", "Interviews completed", "Not accepting applications"]
        record["recruitmentStatus"] = next((state for state in states if header and state in header[0]), "Unknown")
        records.append(record)
    pages = [int(page) for page in re.findall(r"[?&]page=([0-9]+)", document)]
    return {"positions": records, "pageCount": max(pages, default=1)}


def screen_openpostdoc(record: dict) -> tuple[bool, str]:
    """Economics + relevant interdisciplinary roles; no FT50 gate and no hard-coded IDs."""
    if record.get("region") != "eu":
        return False, "Outside Europe"
    title = record.get("title") or ""
    notes = record.get("notes") or ""
    fields = {record.get("primaryField"), *(record.get("secondaryFields") or [])}
    # Three observed feed taxonomy errors. Semantic exclusions generalize to future duplicates.
    if re.search(r"flexure[- ]mechanism|embodiment.*education|mechanistic understanding of AI reasoning", title, re.I):
        return False, "Economics feed label conflicts with the actual engineering/educational-science/AI-only topic"
    if "Economics" in fields:
        return True, "Economics in reference taxonomy, after field-quality check"
    if re.search(r"economics|econometrics|banking|finance|labou?r markets?|entrepreneurship|Janeway", title, re.I):
        return True, "Explicit economics/finance/labour/entrepreneurship research title"
    if re.search(r"economic inactivity|research group.*(?:labor markets|labour markets)|Faculty of Economics|Department of Economics", notes, re.I):
        return True, "Research context explicitly in economics/labour"
    return False, "No evidence of economics/finance/labour research in the public record"


def screen_ejm(record: dict) -> tuple[bool, str]:
    location = record.get("Location of job") or ""
    if not any(re.search(r"(?:,\s*|^)[^,]*\b" + re.escape(country) + r"\b", location) for country in EUROPE_COUNTRIES):
        return False, "Outside Europe"
    if record.get("Degree required") != "Doctorate":
        return False, "Not a doctorate-level role"
    title = record.get("title") or ""
    position_type = record.get("positionTypesAndFields") or ""
    if re.search(r"post[- ]?doc|research fellow|research associate|research assistant|fellowship", title, re.I) or "Postdoctoral Scholar" in position_type:
        return True, "Doctorate-level postdoctoral/fellowship research role in the economics market"
    return False, "Faculty-only/other role outside postdoc scope"


def application_status(record: dict, today: str) -> str:
    """Recruitment may continue after applications close; future display-end is not an open deadline."""
    if record.get("deadline") and record["deadline"] < today:
        return "Closed"
    state = record.get("recruitmentStatus") or record.get("statusKind")
    if state in ("Position filled", "Reviewing applications", "Scheduling interviews", "Arranging flyouts", "Making offers", "Search cancelled", "Search completed", "Interviews completed", "Not accepting applications", "closed", "recently_closed"):
        return "Closed"
    if state == "Accepting applications":
        return "Open"
    # A third-party confirmed_open label alone does not independently confirm the employer.
    return "Uncertain"


def collect_public_benchmarks(get_html: Callable[[str], str] = get_public_html, max_workers: int = 5) -> dict:
    """Fetch complete public pagination, or raise rather than publish silently partial coverage."""
    op_first = {}
    for tab in ("positions", "expired"):
        url = OPENPOSTDOC + "?size=100" + ("&tab=expired" if tab == "expired" else "")
        op_first[tab] = parse_openpostdoc_html(get_html(url))
    op_tasks = [(tab, page, OPENPOSTDOC + "?size=100" + ("&tab=expired" if tab == "expired" else "") + "&page=" + str(page))
                for tab in op_first for page in range(2, op_first[tab]["metadata"]["pageCount"] + 1)]
    op_records = [dict(record, benchmarkTab=tab) for tab in op_first for record in op_first[tab]["positions"]]
    def fetch_op(task):
        tab, page, url = task
        decoded = parse_openpostdoc_html(get_html(url))
        if decoded["metadata"]["page"] != page:
            raise ValueError("OpenPostdoc returned the wrong page")
        return [dict(record, benchmarkTab=tab) for record in decoded["positions"]]
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        for records in pool.map(fetch_op, op_tasks):
            op_records.extend(records)
    expected = sum(first["metadata"]["total"] for first in op_first.values())
    unique_op = {record["id"]: record for record in op_records}
    if len(unique_op) != expected:
        raise RuntimeError(f"Incomplete/inconsistent OpenPostdoc snapshot: {len(unique_op)} unique records; expected {expected}. Retain the last good published snapshot and retry.")
    ejm_first = {kind: parse_ejm_html(get_html(f"{EJM}/{kind}?page=1"), f"{EJM}/{kind}?page=1") for kind in ("statuses", "positions")}
    ejm_tasks = [(kind, page, f"{EJM}/{kind}?page={page}") for kind in ejm_first for page in range(2, ejm_first[kind]["pageCount"] + 1)]
    ejm_records = [dict(record, listingKind=kind) for kind in ejm_first for record in ejm_first[kind]["positions"]]
    def fetch_ejm(task):
        kind, page, url = task
        decoded = parse_ejm_html(get_html(url), url)
        if not decoded["positions"]:
            raise RuntimeError(f"EJM unexpectedly empty page {url}; retain prior snapshot")
        return [dict(record, listingKind=kind) for record in decoded["positions"]]
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        for records in pool.map(fetch_ejm, ejm_tasks):
            ejm_records.extend(records)
    unique_ejm = {}
    for record in ejm_records:
        if record["id"] not in unique_ejm:
            unique_ejm[record["id"]] = dict(record, listingUrls=[record["statusSourceUrl"]])
        elif record["statusSourceUrl"] not in unique_ejm[record["id"]]["listingUrls"]:
            unique_ejm[record["id"]]["listingUrls"].append(record["statusSourceUrl"])
    matched_op = [record for record in unique_op.values() if screen_openpostdoc(record)[0]]
    matched_ejm = [record for record in unique_ejm.values() if screen_ejm(record)[0]]
    return {
        "checkedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
        "metadata": {
            "OpenPostdoc": {"active": op_first["positions"]["metadata"]["total"], "archived": op_first["expired"]["metadata"]["total"], "rawFetched": len(unique_op), "pagesFetched": 2 + len(op_tasks), "matched": len(matched_op)},
            "EconJobMarket": {"rawUniqueFetched": len(unique_ejm), "statusesPages": ejm_first["statuses"]["pageCount"], "activePositionsPages": ejm_first["positions"]["pageCount"], "statusesRecords": len({record["id"] for record in ejm_records if record["listingKind"] == "statuses"}), "activePositionsRecords": len({record["id"] for record in ejm_records if record["listingKind"] == "positions"}), "matched": len(matched_ejm), "note": "Public pagination only; login-only/free advertisements cannot be inferred."},
        },
        "openpostdocMatches": matched_op,
        "ejmMatches": matched_ejm,
        "scopedReferenceIds": {"OpenPostdoc": sorted(record["id"] for record in matched_op), "EconJobMarket": sorted(record["id"] for record in matched_ejm)},
    }
