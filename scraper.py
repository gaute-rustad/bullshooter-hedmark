import os
import re
import json
import urllib.request
from bs4 import BeautifulSoup

BASE_URL = "https://bullshooter.no"
CATEGORY_URL = f"{BASE_URL}/index.php/liga/ligaspill-hedmark/hedmark-c"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def fetch_html(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode('utf-8', errors='ignore')

def clean_cell(text):
    return re.sub(r'\s+', ' ', text.replace('\xa0', ' ')).strip()

def parse_category_page(html):
    soup = BeautifulSoup(html, "html.parser")
    tabell_url = None
    totalsnitt_url = None
    latest_round_url = None
    latest_round_num = 0
    latest_round_date = ""

    for a in soup.find_all("a", href=True):
        href = a['href']
        full_href = href if href.startswith("http") else BASE_URL + href
        text = clean_cell(a.get_text())
        combined = f"{href} {text}".lower()

        if "hedmark-c" in href:
            if "tabell" in combined and not tabell_url:
                tabell_url = full_href
            if "totalsnitt" in combined and not totalsnitt_url:
                totalsnitt_url = full_href
            
            m = re.search(r'runde[- ](\d+)', combined)
            if m:
                r_num = int(m.group(1))
                if r_num > latest_round_num:
                    latest_round_num = r_num
                    latest_round_url = full_href
                    dm = re.search(r'(\d{2}\.\d{2}\.\d{2})', text)
                    if dm:
                        latest_round_date = dm.group(1)

    return {
        "tabell_url": tabell_url,
        "totalsnitt_url": totalsnitt_url,
        "latest_round_url": latest_round_url,
        "latest_round_num": latest_round_num,
        "latest_round_date": latest_round_date
    }

def parse_tabell_page(html):
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    standings = []
    rounds = {}

    if len(tables) >= 1:
        # Table 0: Team standings
        rows = tables[0].find_all("tr")
        for row in rows:
            cells = [clean_cell(c.get_text()) for c in row.find_all(["td", "th"])]
            if len(cells) >= 7 and cells[0] not in ["Team", "Division: C"] and cells[1] != "":
                try:
                    standings.append({
                        "team": cells[0],
                        "win_pct": float(cells[1].replace(',', '.')),
                        "games": int(cells[2]),
                        "wins": int(cells[3]),
                        "losses": int(cells[4]),
                        "leg_diff": cells[5],
                        "points": int(cells[6])
                    })
                except Exception as e:
                    pass

    if len(tables) >= 2:
        # Table 1: Schedule & match results
        rows = tables[1].find_all("tr")
        current_round = None
        current_date = None

        for row in rows:
            cells = [clean_cell(c.get_text()) for c in row.find_all(["td", "th"])]
            if not cells or len(cells) < 6:
                continue

            # Check if this row introduces a new round
            if cells[0] and cells[0].isdigit():
                current_round = int(cells[0])
                current_date = cells[1]
                if current_round not in rounds:
                    rounds[current_round] = {
                        "round": current_round,
                        "date": current_date,
                        "matches": []
                    }
                continue

            # Match row
            home = cells[2]
            away = cells[3]
            venue = cells[4]
            result = cells[5]
            note = cells[6] if len(cells) > 6 else ""

            if home and away and current_round:
                home_legs = None
                away_legs = None
                is_postponed = "utsatt" in result.lower() or "utsatt" in note.lower()

                res_match = re.search(r'(\d+)\s*-\s*(\d+)', result)
                if res_match:
                    home_legs = int(res_match.group(1))
                    away_legs = int(res_match.group(2))

                rounds[current_round]["matches"].append({
                    "home": home,
                    "away": away,
                    "venue": venue,
                    "result": result,
                    "home_legs": home_legs,
                    "away_legs": away_legs,
                    "postponed": is_postponed,
                    "note": note
                })

    return standings, sorted(rounds.values(), key=lambda r: r["round"])

def parse_totalsnitt_page(html):
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    ppr_stats = []
    mpr_stats = []

    if len(tables) >= 1:
        # Table 0: PPR (501)
        rows = tables[0].find_all("tr")
        for row in rows[1:]:
            cells = [clean_cell(c.get_text()) for c in row.find_all(["td", "th"])]
            if len(cells) >= 17 and cells[0] != "Player":
                try:
                    ppr_stats.append({
                        "player": cells[0],
                        "team": cells[1],
                        "ppr": float(cells[2].replace(',', '.')),
                        "games": int(cells[3]),
                        "wins": int(cells[4]),
                        "lton": int(cells[12]),
                        "hats": int(cells[13]),
                        "hton": int(cells[14]),
                        "ton80": int(cells[15]),
                        "high_out": int(cells[16]) if cells[16].isdigit() else 0
                    })
                except Exception:
                    pass

    if len(tables) >= 2:
        # Table 1: MPR (Cricket)
        rows = tables[1].find_all("tr")
        for row in rows[1:]:
            cells = [clean_cell(c.get_text()) for c in row.find_all(["td", "th"])]
            if len(cells) >= 14 and cells[0] != "Player":
                try:
                    mpr_stats.append({
                        "player": cells[0],
                        "team": cells[1],
                        "mpr": float(cells[2].replace(',', '.')),
                        "games": int(cells[3]),
                        "wins": int(cells[4]),
                        "5mr": int(cells[5]),
                        "6mr": int(cells[6]),
                        "7mr": int(cells[7]),
                        "8mr": int(cells[8]),
                        "9mr": int(cells[9]),
                        "hat": int(cells[10]),
                        "whrse": int(cells[11]),
                        "total_darts": int(cells[12]),
                        "total_marks": int(cells[13])
                    })
                except Exception:
                    pass

    return ppr_stats, mpr_stats

def parse_round_page(html):
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    ppr_improvers = []
    round_ppr = []
    mpr_improvers = []
    round_mpr = []

    # Table 0: PPR Improvement
    if len(tables) >= 1:
        for row in tables[0].find_all("tr")[1:]:
            cells = [clean_cell(c.get_text()) for c in row.find_all(["td", "th"])]
            if len(cells) >= 5 and cells[0] != "Player":
                try:
                    ppr_improvers.append({
                        "player": cells[0],
                        "team": cells[1],
                        "prev_ppr": float(cells[2].replace(',', '.')),
                        "round_ppr": float(cells[3].replace(',', '.')),
                        "improvement": float(cells[4].replace(',', '.'))
                    })
                except Exception:
                    pass

    # Table 1: Round PPR
    if len(tables) >= 2:
        for row in tables[1].find_all("tr")[1:]:
            cells = [clean_cell(c.get_text()) for c in row.find_all(["td", "th"])]
            if len(cells) >= 17 and cells[0] != "Player":
                try:
                    round_ppr.append({
                        "player": cells[0],
                        "team": cells[1],
                        "ppr": float(cells[2].replace(',', '.')),
                        "games": int(cells[3]),
                        "wins": int(cells[4]),
                        "lton": int(cells[12]),
                        "hats": int(cells[13]),
                        "hton": int(cells[14]),
                        "ton80": int(cells[15]),
                        "high_out": int(cells[16]) if cells[16].isdigit() else 0
                    })
                except Exception:
                    pass

    # Table 2: MPR Improvement
    if len(tables) >= 3:
        for row in tables[2].find_all("tr")[1:]:
            cells = [clean_cell(c.get_text()) for c in row.find_all(["td", "th"])]
            if len(cells) >= 5 and cells[0] != "Player":
                try:
                    mpr_improvers.append({
                        "player": cells[0],
                        "team": cells[1],
                        "prev_mpr": float(cells[2].replace(',', '.')),
                        "round_mpr": float(cells[3].replace(',', '.')),
                        "improvement": float(cells[4].replace(',', '.'))
                    })
                except Exception:
                    pass

    # Table 3: Round MPR
    if len(tables) >= 4:
        for row in tables[3].find_all("tr")[1:]:
            cells = [clean_cell(c.get_text()) for c in row.find_all(["td", "th"])]
            if len(cells) >= 14 and cells[0] != "Player":
                try:
                    round_mpr.append({
                        "player": cells[0],
                        "team": cells[1],
                        "mpr": float(cells[2].replace(',', '.')),
                        "games": int(cells[3]),
                        "wins": int(cells[4]),
                        "5mr": int(cells[5]),
                        "6mr": int(cells[6]),
                        "7mr": int(cells[7]),
                        "8mr": int(cells[8]),
                        "9mr": int(cells[9]),
                        "hat": int(cells[10]),
                        "whrse": int(cells[11])
                    })
                except Exception:
                    pass

    return {
        "ppr_improvers": ppr_improvers,
        "round_ppr": round_ppr,
        "mpr_improvers": mpr_improvers,
        "round_mpr": round_mpr
    }

def generate_weekly_summary(data):
    latest_r = data.get("latest_round", {})
    r_num = latest_r.get("number", "?")
    r_date = latest_r.get("date", "")
    
    # Matches from schedule for this round
    schedule = data.get("schedule", [])
    matches_text = []
    for r in schedule:
        if r["round"] == r_num:
            for m in r["matches"]:
                if m["postponed"]:
                    matches_text.append(f"• {m['home']} - {m['away']}: Utsatt ({m['venue']})")
                elif m["home_legs"] is not None and m["away_legs"] is not None:
                    matches_text.append(f"• {m['home']} {m['home_legs']} - {m['away_legs']} {m['away']}")
                else:
                    matches_text.append(f"• {m['home']} vs {m['away']} ({m['venue']})")

    # Top improvers
    impr_ppr = latest_r.get("ppr_improvers", [])
    top_ppr_impr = f"{impr_ppr[0]['player']} ({impr_ppr[0]['team']}): +{impr_ppr[0]['improvement']} (snitt: {impr_ppr[0]['round_ppr']})" if impr_ppr else "Ingen data"
    
    impr_mpr = latest_r.get("mpr_improvers", [])
    top_mpr_impr = f"{impr_mpr[0]['player']} ({impr_mpr[0]['team']}): +{impr_mpr[0]['improvement']} (snitt: {impr_mpr[0]['round_mpr']})" if impr_mpr else "Ingen data"

    # Best round score
    r_ppr = sorted(latest_r.get("round_ppr", []), key=lambda x: x["ppr"], reverse=True)
    best_ppr = f"{r_ppr[0]['player']} ({r_ppr[0]['team']}) - {r_ppr[0]['ppr']} PPR" if r_ppr else "Ingen data"

    r_mpr = sorted(latest_r.get("round_mpr", []), key=lambda x: x["mpr"], reverse=True)
    best_mpr = f"{r_mpr[0]['player']} ({r_mpr[0]['team']}) - {r_mpr[0]['mpr']} MPR" if r_mpr else "Ingen data"

    standings = data.get("standings", [])
    leader = standings[0]["team"] if standings else "Ukjent"

    summary = (
        f"🎯 E-DART HEDMARK C – RUNDE {r_num} ({r_date})\n\n"
        f"🏆 KAMPRESULTATER:\n" + ("\n".join(matches_text) if matches_text else "Ingen kampdata registrert") + "\n\n"
        f"⭐ UKENS KLATRERE:\n"
        f"• 501: {top_ppr_impr}\n"
        f"• Cricket: {top_mpr_impr}\n\n"
        f"🔥 UKENS BESTE ENKELTRUNDER:\n"
        f"• Høyest 501: {best_ppr}\n"
        f"• Høyest Cricket: {best_mpr}\n\n"
        f"📊 TABELLTOPPEN: {leader} leder ligaen med {standings[0]['points'] if standings else 0} poeng.\n\n"
        f"Se full tabell og alle spillersnitt i dashboardet!"
    )
    return summary

def send_ntfy(summary, topic, title=None, click_url=None):
    if not topic:
        return
    url = f"https://ntfy.sh/{topic}"
    headers = {
        "Title": title.encode('utf-8') if title else b"E-Dart Hedmark C Oppdatert",
        "Priority": "default",
        "Tags": "dart,trophy"
    }
    if click_url:
        headers["Click"] = click_url
    
    req = urllib.request.Request(url, data=summary.encode('utf-8'), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            print("ntfy notification sent successfully:", resp.status)
    except Exception as e:
        print("Failed to send ntfy notification:", e)

def main():
    print("Scraping category page...")
    cat_html = fetch_html(CATEGORY_URL)
    cat_info = parse_category_page(cat_html)
    print("Category links:", cat_info)

    if not cat_info["tabell_url"]:
        print("Error: Could not find tabell URL")
        return

    print("Fetching tabell...")
    tabell_html = fetch_html(cat_info["tabell_url"])
    standings, schedule = parse_tabell_page(tabell_html)

    print(f"Standings count: {len(standings)}, Schedule rounds: {len(schedule)}")

    ppr_stats = []
    mpr_stats = []
    if cat_info["totalsnitt_url"]:
        print("Fetching totalsnitt...")
        snitt_html = fetch_html(cat_info["totalsnitt_url"])
        ppr_stats, mpr_stats = parse_totalsnitt_page(snitt_html)
        print(f"PPR players: {len(ppr_stats)}, MPR players: {len(mpr_stats)}")

    round_data = {}
    if cat_info["latest_round_url"]:
        print(f"Fetching latest round ({cat_info['latest_round_num']})...")
        r_html = fetch_html(cat_info["latest_round_url"])
        round_data = parse_round_page(r_html)
        round_data["number"] = cat_info["latest_round_num"]
        round_data["date"] = cat_info["latest_round_date"]

    data = {
        "updated_at": cat_info["latest_round_date"] or "Ukjent",
        "standings": standings,
        "schedule": schedule,
        "players_ppr": ppr_stats,
        "players_mpr": mpr_stats,
        "latest_round": round_data
    }

    weekly_summary = generate_weekly_summary(data)
    data["weekly_summary"] = weekly_summary

    output_path = os.path.join(os.path.dirname(__file__), "data.json")
    
    # Check if there is new data compared to previous data.json
    has_changes = True
    prev_latest_round = 0
    if os.path.exists(output_path):
        try:
            with open(output_path, "r", encoding="utf-8") as prev_f:
                prev_data = json.load(prev_f)
                prev_latest_round = prev_data.get("latest_round", {}).get("number", 0)
                # If round number is the same and standings are identical, no new data
                if (prev_latest_round == round_data.get("number") and 
                    prev_data.get("standings") == standings and
                    prev_data.get("latest_round") == round_data):
                    has_changes = False
        except Exception:
            pass

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Wrote data to {output_path}")

    js_path = os.path.join(os.path.dirname(__file__), "data.js")
    with open(js_path, "w", encoding="utf-8") as f:
        f.write("window.EMBEDDED_DATA = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n")
    print(f"Wrote JS fallback to {js_path}")

    summary_path = os.path.join(os.path.dirname(__file__), "weekly_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(weekly_summary)
    print(f"Wrote weekly summary to {summary_path}")

    # ntfy notification if env var present AND there are new results
    ntfy_topic = os.environ.get("NTFY_TOPIC")
    force_notify = os.environ.get("FORCE_NOTIFY", "").lower() in ["1", "true", "yes"]
    
    if ntfy_topic:
        if has_changes or force_notify:
            print("New round/data detected! Sending ntfy notification...")
            gh_pages_url = os.environ.get("GH_PAGES_URL", "")
            send_ntfy(weekly_summary, ntfy_topic, title=f"🎯 Hedmark C: Runde {cat_info['latest_round_num']} er publisert!", click_url=gh_pages_url)
        else:
            print("No new round data detected since last scrape, skipping ntfy.")

if __name__ == "__main__":
    main()
