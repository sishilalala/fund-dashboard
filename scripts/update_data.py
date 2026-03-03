#!/usr/bin/env python3
"""
\u6bcf\u65e5\u81ea\u52a8\u91c7\u96c6\u516c\u52df\u57fa\u91d1\u6570\u636e\uff0c\u751f\u6210 data.js
\u6570\u636e\u6765\u6e90\uff1aAKShare\uff08\u4e1c\u65b9\u8d22\u5bcc/\u5929\u5929\u57fa\u91d1\uff09\u3001\u65b0\u6d6a\u8d22\u7ecf
"""
import json
import re
import sys
from datetime import datetime

import akshare as ak
import pandas as pd
import requests
from urllib.parse import quote


def fetch_indices():
    """\u83b7\u53d6A\u80a1\u4e3b\u8981\u6307\u6570"""
    print("Fetching A-share indices...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://quote.eastmoney.com/",
    }
    url = "https://push2.eastmoney.com/api/qt/ulist.np/get"
    params = {
        "fltt": 2,
        "secids": "1.000001,0.399001,0.399006,1.000300,1.000688,1.000016,0.899050",
        "fields": "f1,f2,f3,f4,f5,f6,f7,f8,f12,f13,f14,f15,f16,f17,f18",
        "ut": "fa5fd1943c7b386f172d6893dbfba10b",
    }
    name_map = {
        "000001": "\u4e0a\u8bc1\u6307\u6570", "399001": "\u6df7\u8bc1\u6210\u6307", "399006": "\u521b\u4e1a\u677f\u6307",
        "000300": "\u6caa\u6df1300", "000688": "\u79d1\u521b50", "000016": "\u4e0a\u8bc150", "899050": "\u5317\u8bc150",
    }
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        data = resp.json()
        if data.get("data") and data["data"].get("diff"):
            indices = []
            for item in data["data"]["diff"]:
                code = item.get("f12", "")
                indices.append({
                    "code": code,
                    "name": name_map.get(code, item.get("f14", "")),
                    "price": item.get("f2", 0),
                    "change_pct": item.get("f3", 0),
                    "change_amt": item.get("f4", 0),
                    "volume": item.get("f6", 0),
                    "high": item.get("f15", 0),
                    "low": item.get("f16", 0),
                    "open": item.get("f17", 0),
                    "prev_close": item.get("f18", 0),
                    "amplitude": item.get("f7", 0),
                })
            print(f"  Got {len(indices)} indices")
            return indices
    except Exception as e:
        print(f"  Error: {e}")
    return []


def fetch_industry_boards():
    """\u83b7\u53d6\u884c\u4e1a\u677f\u5757\u6da8\u8dcc\u6392\u540d\uff08\u65b0\u6d6a\u8d22\u7ecf\uff09"""
    print("Fetching industry boards...")
    try:
        url = "https://vip.stock.finance.sina.com.cn/q/view/newSinaHy.php"
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        match = re.search(r"=\s*({.*})", resp.text, re.DOTALL)
        if match:
            raw = json.loads(match.group(1))
            boards = []
            for key, val in raw.items():
                parts = val.split(",")
                if len(parts) >= 13:
                    boards.append({
                        "name": parts[1],
                        "stock_count": int(parts[2]),
                        "change_pct": round(float(parts[5]), 2),
                        "volume": int(parts[6]),
                        "amount": int(parts[7]),
                        "leader_name": parts[12],
                        "leader_change_pct": round(float(parts[9]), 2),
                    })
            boards.sort(key=lambda x: x["change_pct"], reverse=True)
            print(f"  Got {len(boards)} boards")
            return boards
    except Exception as e:
        print(f"  Error: {e}")
    return []


def fetch_fund_flow():
    """\u83b7\u53d6\u5927\u76d8\u8d44\u91d1\u6d41\u5411\uff08\u6700\u8fd15\u5929\uff09"""
    print("Fetching market fund flow...")
    try:
        df = ak.stock_market_fund_flow()
        flows = []
        for _, row in df.tail(5).iterrows():
            flows.append({
                "date": str(row["\u65e5\u671f"])[:10],
                "sh_close": round(float(row["\u4e0a\u8bc1-\u6536\u76d8\u4ef7"]), 2),
                "sh_change": round(float(row["\u4e0a\u8bc1-\u6da8\u8dcc\u5e45"]), 2),
                "sz_close": round(float(row["\u6df7\u8bc1-\u6536\u76d8\u4ef7"]), 2),
                "sz_change": round(float(row["\u6df7\u8bc1-\u6da8\u8dcc\u5e45"]), 2),
                "main_net_inflow": round(float(row["\u4e3b\u529b\u51c0\u6d41\u5165-\u51c0\u989d"]) / 1e8, 2),
                "main_net_pct": round(float(row["\u4e3b\u529b\u51c0\u6d41\u5165-\u51c0\u5360\u6bd4"]), 2),
                "super_large_net": round(float(row["\u8d85\u5927\u5355\u51c0\u6d41\u5165-\u51c0\u989d"]) / 1e8, 2),
                "large_net": round(float(row["\u5927\u5355\u51c0\u6d41\u5165-\u51c0\u989d"]) / 1e8, 2),
                "medium_net": round(float(row["\u4e2d\u5355\u51c0\u6d41\u5165-\u51c0\u989d"]) / 1e8, 2),
                "small_net": round(float(row["\u5c0f\u5355\u51c0\u6d41\u5165-\u51c0\u989d"]) / 1e8, 2),
            })
        print(f"  Got {len(flows)} days")
        return flows
    except Exception as e:
        print(f"  Error: {e}")
    return []


def classify_fund(name):
    name = str(name)
    if any(k in name for k in ["\u6307\u6570", "ETF", "LOF"]):
        return "\u6307\u6570\u578b"
    if any(k in name for k in ["\u503a", "\u4fe1\u7528", "\u5229\u7387", "\u7eaf\u503a"]):
        return "\u503a\u5238\u578b"
    if any(k in name for k in ["\u6df7\u5408", "\u914d\u7f6e", "\u5e73\u8861", "\u7075\u6d3b"]):
        return "\u6df7\u5408\u578b"
    if any(k in name for k in ["\u80a1\u7968", "\u6210\u957f", "\u4ef7\u503c"]):
        return "\u80a1\u7968\u578b"
    if any(k in name for k in ["QDII", "\u7f8e\u56fd", "\u7f8e\u5143", "\u6e2f\u80a1", "\u5168\u7403", "\u4e9a\u592a", "\u6052\u751f", "\u7eb3\u65af\u8fbe\u514b", "\u6807\u666e"]):
        return "QDII"
    if any(k in name for k in ["FOF", "\u517b\u8001"]):
        return "FOF"
    return "\u5176\u4ed6"


def fetch_top_funds():
    """\u83b7\u53d6\u5168\u90e8\u57fa\u91d1\u6da8\u5e45 Top 50"""
    print("Fetching top 50 funds (all types)...")
    try:
        df = ak.fund_open_fund_rank_em(symbol="\u5168\u90e8")
        df["\u65e5\u589e\u957f\u7387"] = pd.to_numeric(df["\u65e5\u589e\u957f\u7387"], errors="coerce")
        df = df.dropna(subset=["\u65e5\u589e\u957f\u7387"]).sort_values("\u65e5\u589e\u957f\u7387", ascending=False)
        funds = []
        for _, row in df.head(50).iterrows():
            funds.append({
                "code": str(row["\u57fa\u91d1\u4ee3\u7801"]),
                "name": str(row["\u57fa\u91d1\u7b80\u79f0"]),
                "date": str(row["\u65e5\u671f"]),
                "nav": round(float(row["\u5355\u4f4d\u51c0\u503c"]), 4) if pd.notna(row["\u5355\u4f4d\u51c0\u503c"]) else None,
                "acc_nav": round(float(row["\u7d2f\u8ba1\u51c0\u503c"]), 4) if pd.notna(row["\u7d2f\u8ba1\u51c0\u503c"]) else None,
                "daily_return": round(float(row["\u65e5\u589e\u957f\u7387"]), 2),
                "week_1": round(float(row["\u8fd11\u5468"]), 2) if pd.notna(row["\u8fd11\u5468"]) else None,
                "month_1": round(float(row["\u8fd11\u6708"]), 2) if pd.notna(row["\u8fd11\u6708"]) else None,
                "month_3": round(float(row["\u8fd13\u6708"]), 2) if pd.notna(row["\u8fd13\u6708"]) else None,
                "month_6": round(float(row["\u8fd16\u6708"]), 2) if pd.notna(row["\u8fd16\u6708"]) else None,
                "year_1": round(float(row["\u8fd11\u5e74"]), 2) if pd.notna(row["\u8fd11\u5e74"]) else None,
                "ytd": round(float(row["\u4eca\u5e74\u6765"]), 2) if pd.notna(row["\u4eca\u5e74\u6765"]) else None,
                "since_inception": round(float(row["\u6210\u7acb\u6765"]), 2) if pd.notna(row["\u6210\u7acb\u6765"]) else None,
                "fee": str(row["\u624b\u7eed\u8d39"]) if pd.notna(row["\u624b\u7eed\u8d39"]) else None,
                "type": classify_fund(row["\u57fa\u91d1\u7b80\u79f0"]),
            })
        print(f"  Got {len(funds)} funds")
        return funds
    except Exception as e:
        print(f"  Error: {e}")
    return []


def fetch_category_funds():
    """\u83b7\u53d6\u5404\u7c7b\u578b\u57fa\u91d1 Top 30"""
    print("Fetching per-category top 30...")
    category_funds = {}
    for symbol in ["\u80a1\u7968\u578b", "\u6df7\u5408\u578b", "\u503a\u5238\u578b", "\u6307\u6570\u578b", "QDII", "FOF"]:
        try:
            df = ak.fund_open_fund_rank_em(symbol=symbol)
            df["\u65e5\u589e\u957f\u7387"] = pd.to_numeric(df["\u65e5\u589e\u957f\u7387"], errors="coerce")
            df = df.dropna(subset=["\u65e5\u589e\u957f\u7387"]).sort_values("\u65e5\u589e\u957f\u7387", ascending=False)
            top = []
            for _, row in df.head(30).iterrows():
                top.append({
                    "code": str(row["\u57fa\u91d1\u4ee3\u7801"]),
                    "name": str(row["\u57fa\u91d1\u7b80\u79f0"]),
                    "daily_return": round(float(row["\u65e5\u589e\u957f\u7387"]), 2),
                    "week_1": round(float(row["\u8fd11\u5468"]), 2) if pd.notna(row["\u8fd11\u5468"]) else None,
                    "month_1": round(float(row["\u8fd11\u6708"]), 2) if pd.notna(row["\u8fd11\u6708"]) else None,
                    "month_3": round(float(row["\u8fd13\u6708"]), 2) if pd.notna(row["\u8fd13\u6708"]) else None,
                    "month_6": round(float(row["\u8fd16\u6708"]), 2) if pd.notna(row["\u8fd16\u6708"]) else None,
                    "year_1": round(float(row["\u8fd11\u5e74"]), 2) if pd.notna(row["\u8fd11\u5e74"]) else None,
                    "ytd": round(float(row["\u4eca\u5e74\u6765"]), 2) if pd.notna(row["\u4eca\u5e74\u6765"]) else None,
                    "fee": str(row["\u624b\u7eed\u8d39"]) if pd.notna(row["\u624b\u7eed\u8d39"]) else None,
                })
            category_funds[symbol] = top
            print(f"  {symbol}: {len(top)} funds")
        except Exception as e:
            print(f"  {symbol} Error: {e}")
    return category_funds


def fetch_news():
    """\u83b7\u53d6\u57fa\u91d1\u884c\u4e1a\u8981\u95fb\uff08\u4ece\u591a\u4e2a\u6743\u5a01\u8d22\u7ecf\u5a92\u4f53\uff09"""
    print("Fetching fund industry news...")
    news_items = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    today = datetime.now().strftime("%Y-%m-%d")

    # Source 1: \u4e1c\u65b9\u8d22\u5bcc\u57fa\u91d1\u65b0\u95fb API
    try:
        em_url = "https://newsapi.eastmoney.com/kuaixun/v1/getlist_102_ajaxResult_50_1_.html"
        resp = requests.get(em_url, headers=headers, timeout=15)
        text = resp.text
        # Parse the JSONP callback
        match = re.search(r'\((.+)\)', text, re.DOTALL)
        if match:
            em_data = json.loads(match.group(1))
            live_list = em_data.get("LivesList", [])
            for item in live_list[:20]:
                title = item.get("title", "").strip()
                digest = item.get("digest", "").strip()
                url = item.get("url_w", item.get("url_m", ""))
                pub_date = item.get("showtime", today)[:10]
                if title and any(kw in title + digest for kw in [
                    "\u57fa\u91d1", "ETF", "\u516c\u52df", "\u79c1\u52df", "\u57fa\u6c11", "\u51c0\u503c", "\u7533\u8d2d",
                    "\u8d4e\u56de", "FOF", "QDII", "\u6307\u6570", "\u503a\u57fa", "\u6df7\u5408"
                ]):
                    category = classify_news(title + digest)
                    news_items.append({
                        "title": title,
                        "summary": digest[:200] if digest else title,
                        "source": "\u4e1c\u65b9\u8d22\u5bcc\u7f51",
                        "date": pub_date,
                        "url": url,
                        "category": category,
                    })
        print(f"  \u4e1c\u65b9\u8d22\u5bcc: {len(news_items)} items")
    except Exception as e:
        print(f"  \u4e1c\u65b9\u8d22\u5bcc Error: {e}")

    # Source 2: \u65b0\u6d6a\u8d22\u7ecf\u57fa\u91d1\u9891\u9053
    try:
        sina_url = "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2516&etime=0&stime=0&ctime=0&date=&k=&num=30&page=1"
        resp = requests.get(sina_url, headers=headers, timeout=15)
        sina_data = resp.json()
        sina_list = sina_data.get("result", {}).get("data", [])
        count_sina = 0
        for item in sina_list:
            title = item.get("title", "").strip()
            intro = item.get("intro", "").strip()
            url = item.get("url", "")
            ctime = item.get("ctime", "")
            pub_date = ctime[:10] if ctime else today
            if title and any(kw in title + intro for kw in [
                "\u57fa\u91d1", "ETF", "\u516c\u52df", "\u79c1\u52df", "\u57fa\u6c11", "\u51c0\u503c", "\u7533\u8d2d",
                "\u8d4e\u56de", "FOF", "QDII", "\u6307\u6570\u578b", "\u503a\u57fa", "\u6df7\u5408"
            ]):
                # Skip duplicates
                if not any(n["title"] == title for n in news_items):
                    category = classify_news(title + intro)
                    news_items.append({
                        "title": title,
                        "summary": intro[:200] if intro else title,
                        "source": "\u65b0\u6d6a\u8d22\u7ecf",
                        "date": pub_date,
                        "url": url,
                        "category": category,
                    })
                    count_sina += 1
        print(f"  \u65b0\u6d6a\u8d22\u7ecf: {count_sina} items")
    except Exception as e:
        print(f"  \u65b0\u6d6a\u8d22\u7ecf Error: {e}")

    # Source 3: \u540c\u82b1\u987a\u57fa\u91d1\u9891\u9053
    try:
        ths_url = "https://news.10jqka.com.cn/tapp/news/push/stock/?page=1&tag=webFund&track=website&pagesize=20"
        resp = requests.get(ths_url, headers={**headers, "Referer": "https://fund.10jqka.com.cn/"}, timeout=15)
        ths_data = resp.json()
        ths_list = ths_data.get("data", {}).get("list", [])
        count_ths = 0
        for item in ths_list:
            title = item.get("title", "").strip()
            digest = item.get("digest", "").strip()
            url = item.get("url", "")
            ctime = item.get("ctime", "")
            pub_date = ctime[:10] if ctime else today
            if title and not any(n["title"] == title for n in news_items):
                category = classify_news(title + digest)
                news_items.append({
                    "title": title,
                    "summary": digest[:200] if digest else title,
                    "source": "\u540c\u82b1\u987a",
                    "date": pub_date,
                    "url": url,
                    "category": category,
                })
                count_ths += 1
        print(f"  \u540c\u82b1\u987a: {count_ths} items")
    except Exception as e:
        print(f"  \u540c\u82b1\u987a Error: {e}")

    # Deduplicate and sort by date desc, take top 15
    seen_titles = set()
    unique_news = []
    for n in news_items:
        short_title = n["title"][:20]
        if short_title not in seen_titles:
            seen_titles.add(short_title)
            unique_news.append(n)

    unique_news.sort(key=lambda x: x["date"], reverse=True)
    result = unique_news[:15]
    print(f"  Total unique news: {len(result)}")
    return result


def classify_news(text):
    """\u6839\u636e\u6587\u672c\u5185\u5bb9\u5206\u7c7b\u65b0\u95fb"""
    text = str(text)
    if any(k in text for k in ["\u76d1\u7ba1", "\u8bc1\u76d1\u4f1a", "\u89c4\u5219", "\u6307\u5f15", "\u6cd5\u89c4", "\u5408\u89c4", "\u5904\u7f5a", "\u65b0\u89c4", "\u653f\u7b56", "\u65bd\u884c"]):
        return "\u76d1\u7ba1\u653f\u7b56"
    if any(k in text for k in ["\u53d1\u884c", "\u65b0\u57fa\u91d1", "\u52df\u96c6", "\u7533\u62a5", "\u83b7\u6279", "\u6210\u7acb", "\u8ba4\u8d2d"]):
        return "\u57fa\u91d1\u53d1\u884c"
    if any(k in text for k in ["\u4eba\u4e8b", "\u79bb\u4efb", "\u4e0a\u4efb", "\u53d8\u66f4", "\u603b\u7ecf\u7406", "\u8463\u4e8b", "\u57fa\u91d1\u7ecf\u7406", "\u79bb\u804c"]):
        return "\u4eba\u4e8b\u53d8\u52a8"
    if any(k in text for k in ["QDII", "\u6d77\u5916", "\u7f8e\u80a1", "\u6e2f\u80a1", "\u5168\u7403", "\u7eb3\u65af\u8fbe\u514b", "\u6807\u666e", "\u56fd\u9645"]):
        return "\u56fd\u9645\u89c6\u89d2"
    if any(k in text for k in ["\u5206\u6790", "\u7814\u62a5", "\u5c55\u671b", "\u7b56\u7565", "\u914d\u7f6e", "\u7814\u7a76", "\u89c2\u70b9", "\u5224\u65ad", "\u8d8b\u52bf"]):
        return "\u884c\u4e1a\u5206\u6790"
    return "\u5e02\u573a\u52a8\u6001"


def main():
    data = {}
    data["indices"] = fetch_indices()
    data["industry_boards"] = fetch_industry_boards()
    data["fund_flow"] = fetch_fund_flow()
    data["top_funds"] = fetch_top_funds()
    data["category_funds"] = fetch_category_funds()
    data["news"] = fetch_news()
    data["metadata"] = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "trading_date": data["top_funds"][0]["date"] if data["top_funds"] else datetime.now().strftime("%Y-%m-%d"),
    }

    # Write chunked data files (to avoid GitHub API size limits)
    # data-market.js
    market = {"indices": data["indices"], "industry_boards": data["industry_boards"], "fund_flow": data["fund_flow"]}
    write_js_file("data-market.js", "FUND_DATA_MARKET", market)

    # data-top-funds.js
    write_js_file("data-top-funds.js", "FUND_DATA_TOP", {"top_funds": data["top_funds"]})

    # data-cat1.js (\u80a1\u7968\u578b, \u6df7\u5408\u578b, \u503a\u5238\u578b)
    cat1 = {k: data["category_funds"].get(k, []) for k in ["\u80a1\u7968\u578b", "\u6df7\u5408\u578b", "\u503a\u5238\u578b"]}
    write_js_file("data-cat1.js", "FUND_DATA_CAT1", cat1)

    # data-cat2.js (\u6307\u6570\u578b, QDII, FOF)
    cat2 = {k: data["category_funds"].get(k, []) for k in ["\u6307\u6570\u578b", "QDII", "FOF"]}
    write_js_file("data-cat2.js", "FUND_DATA_CAT2", cat2)

    # data-news.js
    write_js_file("data-news.js", "FUND_DATA_NEWS", {"news": data["news"]})

    # data-meta.js
    write_js_file("data-meta.js", "FUND_DATA_META", {"metadata": data["metadata"]})

    print("\nAll data chunk files written.")


def write_js_file(filename, var_name, obj):
    js = f"const {var_name} = " + json.dumps(obj, ensure_ascii=False, indent=2) + ";\n"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(js)
    print(f"  {filename} written ({len(js)/1024:.1f} KB)")


if __name__ == "__main__":
    main()
