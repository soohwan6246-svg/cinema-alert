import os
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta, timezone

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)
LOTTE_URL = "https://www.lottecinema.co.kr/LCWS/Ticketing/TicketingData.aspx"
MEGABOX_URL = "https://www.megabox.co.kr/on/oh/ohb/SimpleBooking/selectBokdList.do"
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notified_state.json")

# =========================================================================
# 설정 (원하는 영화/지점으로 자유롭게 수정 가능)
# =========================================================================
KEYWORDS = ["둠스데이", "doomsday"]
LOTTE_BRANCH_NAME = "월드타워"     # 예: "월드타워", "건대입구" (사용 안 하려면 "")
MEGABOX_BRANCH_NAME = "코엑스"     # 예: "코엑스", "강남" (사용 안 하려면 "")
SCREEN_FILTERS = []                # 비워두면 모든 상영관 감시 (예: ["돌비", "수퍼플렉스"])
WATCH_GLOBAL_MOVIE_LIST = True     # 예매 영화 목록 최초 등록 시 즉시 알림


def match_keywords(text, keywords):
    if not text or not keywords:
        return False
    low = text.lower().replace(" ", "")
    for kw in keywords:
        k = kw.strip().lower().replace(" ", "")
        if k and k in low:
            return True
    return False


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return set(data)
        except Exception:
            pass
    return set()


def save_state(keys_set):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(keys_set), f, ensure_ascii=False, indent=2)


def post_lotte(payload):
    body = ("paramList=" + urllib.parse.quote(json.dumps(payload))).encode("utf-8")
    req = urllib.request.Request(
        LOTTE_URL,
        data=body,
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": "https://www.lottecinema.co.kr/NLCHS/Ticketing",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def post_megabox(payload):
    req = urllib.request.Request(
        MEGABOX_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/json",
            "Referer": "https://www.megabox.co.kr/booking",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def send_discord(webhook_url, message):
    payload = json.dumps({"content": message}).encode("utf-8")
    req = urllib.request.Request(
        webhook_url.strip(),
        data=payload,
        headers={"User-Agent": USER_AGENT, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        print(f"Discord sent: HTTP {resp.status}")


def send_telegram(bot_token, chat_id, message):
    url = f"https://api.telegram.org/bot{bot_token.strip()}/sendMessage"
    payload = json.dumps({"chat_id": chat_id.strip(), "text": message}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        print(f"Telegram sent: HTTP {resp.status}")


def check_lotte(notified):
    found = []
    data = post_lotte({
        "MethodName": "GetTicketingPageTOBE",
        "channelType": "HO",
        "osType": "W",
        "osVersion": USER_AGENT,
        "memberOnNo": "0",
    })

    if WATCH_GLOBAL_MOVIE_LIST:
        for m in data.get("Movies", {}).get("Movies", {}).get("Items", []):
            name = m.get("MovieNameKR") or m.get("MovieNameUS") or ""
            if match_keywords(name, KEYWORDS):
                code = m.get("RepresentationMovieCode", "")
                key = f"LT_GLOBAL|{code}|{name}"
                if key not in notified:
                    notified.add(key)
                    rel = (m.get("ReleaseDate") or "").split(" ")[0] or "미정"
                    found.append(f"🚨 [롯데시네마 예매 목록 등록!] {name} (개봉일: {rel})")

    if LOTTE_BRANCH_NAME:
        cinemas = data.get("Cinemas", {}).get("Cinemas", {}).get("Items", [])
        target_id = None
        for c in cinemas:
            cname = c.get("CinemaNameKR") or c.get("CinemaName") or ""
            if cname == LOTTE_BRANCH_NAME:
                target_id = f"{c.get('DivisionCode', 1)}|{c.get('DetailDivisionCode', '0001')}|{c.get('CinemaID')}"
                break

        play_dates = [
            d.get("PlayDate")
            for d in data.get("MoviePlayDates", {}).get("Items", {}).get("Items", [])
            if d.get("IsPlayDate") == "Y" and d.get("PlayDate")
        ]

        if target_id:
            for pdate in play_dates[:10]:
                seq_data = post_lotte({
                    "MethodName": "GetPlaySequence",
                    "channelType": "HO",
                    "osType": "W",
                    "osVersion": USER_AGENT,
                    "playDate": pdate,
                    "cinemaID": target_id,
                    "representationMovieCode": "",
                })
                for it in seq_data.get("PlaySeqs", {}).get("Items", []):
                    movie = it.get("MovieNameKR", "")
                    if not match_keywords(movie, KEYWORDS):
                        continue
                    screen = it.get("ScreenNameKR", "")
                    screen_div = it.get("ScreenDivisionNameKR", "")
                    if SCREEN_FILTERS and not match_keywords(f"{screen} {screen_div}", SCREEN_FILTERS):
                        continue
                    key = f"LT_SEQ|{LOTTE_BRANCH_NAME}|{pdate}|{it.get('StartTime')}|{screen}|{movie}"
                    if key not in notified:
                        notified.add(key)
                        found.append(
                            f"🎟️ [롯데시네마 {LOTTE_BRANCH_NAME}] {movie} | {pdate} "
                            f"{it.get('StartTime')}~{it.get('EndTime')} | {screen} "
                            f"(잔여 {it.get('BookingSeatCount', 0)}/{it.get('TotalSeatCount', 0)}석)"
                        )
    return found


def check_megabox(notified):
    found = []
    # Korea Standard Time (UTC+9)
    kst_now = datetime.now(timezone.utc) + timedelta(hours=9)
    today_str = kst_now.strftime("%Y%m%d")
    data = post_megabox({"playDe": today_str, "brchNo1": "1351", "movieNo1": ""})

    if WATCH_GLOBAL_MOVIE_LIST:
        for m in data.get("movieList", []):
            name = m.get("movieNm", "")
            if match_keywords(name, KEYWORDS):
                code = str(m.get("movieNo", ""))
                key = f"MB_GLOBAL|{code}|{name}"
                if key not in notified:
                    notified.add(key)
                    found.append(f"🚨 [메가박스 예매 목록 등록!] {name}")

    if MEGABOX_BRANCH_NAME:
        brch_no = None
        for b in data.get("areaBrchList", []):
            if b.get("brchNm") == MEGABOX_BRANCH_NAME:
                brch_no = str(b.get("brchNo"))
                break

        play_dates = []
        for d in data.get("movieFormDeList", []):
            de = d.get("playDe") if isinstance(d, dict) else str(d)
            if de and len(de) == 8:
                play_dates.append(de)
        if not play_dates:
            play_dates = [(kst_now + timedelta(days=i)).strftime("%Y%m%d") for i in range(7)]

        if brch_no:
            for de in play_dates[:10]:
                seq_data = post_megabox({"playDe": de, "brchNo1": brch_no, "movieNo1": ""})
                pdate_fmt = f"{de[:4]}-{de[4:6]}-{de[6:8]}"
                for it in seq_data.get("movieFormList", []):
                    movie = it.get("movieNm", "")
                    if not match_keywords(movie, KEYWORDS):
                        continue
                    screen = it.get("theabExpoNm", "")
                    if SCREEN_FILTERS and not match_keywords(screen, SCREEN_FILTERS):
                        continue
                    key = f"MB_SEQ|{MEGABOX_BRANCH_NAME}|{pdate_fmt}|{it.get('playStartTime')}|{screen}|{movie}"
                    if key not in notified:
                        notified.add(key)
                        found.append(
                            f"🎟️ [메가박스 {MEGABOX_BRANCH_NAME}] {movie} | {pdate_fmt} "
                            f"{it.get('playStartTime')}~{it.get('playEndTime')} | {screen} "
                            f"(잔여 {it.get('restSeatCnt', 0)}/{it.get('totSeatCnt', 0)}석)"
                        )
    return found


def main():
    notified = load_state()
    prev_count = len(notified)
    all_found = []

    try:
        all_found.extend(check_lotte(notified))
    except Exception as e:
        print(f"Lotte check error: {e}")

    try:
        all_found.extend(check_megabox(notified))
    except Exception as e:
        print(f"Megabox check error: {e}")

    discord_url = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    tg_chat = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

    if all_found:
        msg = "🔥 **어벤져스: 둠스데이 예매 오픈 감지!** 🔥\n\n" + "\n".join(all_found[:15])
        if len(all_found) > 15:
            msg += f"\n... 외 {len(all_found) - 15}건 더 열림"
        print(msg)

        if discord_url:
            send_discord(discord_url, msg)
        if tg_token and tg_chat:
            send_telegram(tg_token, tg_chat, msg)

        if len(notified) != prev_count:
            save_state(notified)
    else:
        print(f"[{datetime.now(timezone.utc) + timedelta(hours=9):%Y-%m-%d %H:%M:%S} KST] 아직 '{', '.join(KEYWORDS)}' 예매 미오픈")
        # 수동 테스트 실행 시 연결 확인용 메시지
        if os.environ.get("SEND_TEST_ON_MANUAL") == "1" and os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch":
            test_msg = (
                "🔔 [GitHub 클라우드 테스트] 《어벤져스: 둠스데이》 감시 봇이 정상 작동 중입니다!\n"
                f"• 감시 극장: 롯데시네마({LOTTE_BRANCH_NAME}) / 메가박스({MEGABOX_BRANCH_NAME})\n"
                "• 현재 상태: 아직 예매 미오픈"
            )
            if discord_url:
                send_discord(discord_url, test_msg)
            if tg_token and tg_chat:
                send_telegram(tg_token, tg_chat, test_msg)


if __name__ == "__main__":
    main()
