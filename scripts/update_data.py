#!/usr/bin/env python3
"""
每日自动采集公募基金数据，生成 data.js
数据来源：AKShare（东方财富/天天基金）、新浪财经
"""
import json
import re
import sys
from datetime import datetime

import akshare as ak
import pandas as pd
import requests


def fetch_indices():
    """获取A股主要指数"""
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
        "000001": "上证指数", "399001": "深证成指", "399006": "创业板指",
        "000300": "沪深300", "000688": "科创50", "000016": "上证50", "899050": "北证50",
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
    """获取行业板块涨跌排名（新浪财经）"""
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
    """获取大盘资金流向（最近5天）"""
    print("Fetching market fund flow...")
    try:
        df = ak.stock_market_fund_flow()
        flows = []
        for _, row in df.tail(5).iterrows():
            flows.append({
                "date": str(row["日期"])[:10],
                "sh_close": round(float(row["上证-收盘价"]), 2),
                "sh_change": round(float(row["上证-涨跌幅"]), 2),
                "sz_close": round(float(row["深证-收盘价"]), 2),
                "sz_change": round(float(row["深证-涨跌幅"]), 2),
                "main_net_inflow": round(float(row["主力净流入-净额"]) / 1e8, 2),
                "main_net_pct": round(float(row["主力净流入-净占比"]), 2),
                "super_large_net": round(float(row["超大单净流入-净额"]) / 1e8, 2),
                "large_net": round(float(row["大单净流入-净额"]) / 1e8, 2),
                "medium_net": round(float(row["中单净流入-净额"]) / 1e8, 2),
                "small_net": round(float(row["小单净流入-净额"]) / 1e8, 2),
            })
        print(f"  Got {len(flows)} days")
        return flows
    except Exception as e:
        print(f"  Error: {e}")
    return []


def classify_fund(name):
    name = str(name)
    if any(k in name for k in ["指数", "ETF", "LOF"]):
        return "指数型"
    if any(k in name for k in ["债", "信用", "利率", "纯债"]):
        return "债券型"
    if any(k in name for k in ["混合", "配置", "平衡", "灵活"]):
        return "混合型"
    if any(k in name for k in ["股票", "成长", "价值"]):
        return "股票型"
    if any(k in name for k in ["QDII", "美国", "美元", "港股", "全球", "亚太", "恒生", "纳斯达克", "标普"]):
        return "QDII"
    if any(k in name for k in ["FOF", "养老"]):
        return "FOF"
    return "其他"


def fetch_top_funds():
    """获取全部基金涨幅 Top 50"""
    print("Fetching top 50 funds (all types)...")
    try:
        df = ak.fund_open_fund_rank_em(symbol="全部")
        df["日增长率"] = pd.to_numeric(df["日增长率"], errors="coerce")
        df = df.dropna(subset=["日增长率"]).sort_values("日增长率", ascending=False)
        funds = []
        for _, row in df.head(50).iterrows():
            funds.append({
                "code": str(row["基金代码"]),
                "name": str(row["基金简称"]),
                "date": str(row["日期"]),
                "nav": round(float(row["单位净值"]), 4) if pd.notna(row["单位净值"]) else None,
                "acc_nav": round(float(row["累计净值"]), 4) if pd.notna(row["累计净值"]) else None,
                "daily_return": round(float(row["日增长率"]), 2),
                "week_1": round(float(row["近1周"]), 2) if pd.notna(row["近1周"]) else None,
                "month_1": round(float(row["近1月"]), 2) if pd.notna(row["近1月"]) else None,
                "month_3": round(float(row["近3月"]), 2) if pd.notna(row["近3月"]) else None,
                "month_6": round(float(row["近6月"]), 2) if pd.notna(row["近6月"]) else None,
                "year_1": round(float(row["近1年"]), 2) if pd.notna(row["近1年"]) else None,
                "ytd": round(float(row["今年来"]), 2) if pd.notna(row["今年来"]) else None,
                "since_inception": round(float(row["成立来"]), 2) if pd.notna(row["成立来"]) else None,
                "fee": str(row["手续费"]) if pd.notna(row["手续费"]) else None,
                "type": classify_fund(row["基金简称"]),
            })
        print(f"  Got {len(funds)} funds")
        return funds
    except Exception as e:
        print(f"  Error: {e}")
    return []


def fetch_category_funds():
    """获取各类型基金 Top 30"""
    print("Fetching per-category top 30...")
    category_funds = {}
    for symbol in ["股票型", "混合型", "债券型", "指数型", "QDII", "FOF"]:
        try:
            df = ak.fund_open_fund_rank_em(symbol=symbol)
            df["日增长率"] = pd.to_numeric(df["日增长率"], errors="coerce")
            df = df.dropna(subset=["日增长率"]).sort_values("日增长率", ascending=False)
            top = []
            for _, row in df.head(30).iterrows():
                top.append({
                    "code": str(row["基金代码"]),
                    "name": str(row["基金简称"]),
                    "daily_return": round(float(row["日增长率"]), 2),
                    "week_1": round(float(row["近1周"]), 2) if pd.notna(row["近1周"]) else None,
                    "month_1": round(float(row["近1月"]), 2) if pd.notna(row["近1月"]) else None,
                    "month_3": round(float(row["近3月"]), 2) if pd.notna(row["近3月"]) else None,
                    "month_6": round(float(row["近6月"]), 2) if pd.notna(row["近6月"]) else None,
                    "year_1": round(float(row["近1年"]), 2) if pd.notna(row["近1年"]) else None,
                    "ytd": round(float(row["今年来"]), 2) if pd.notna(row["今年来"]) else None,
                    "fee": str(row["手续费"]) if pd.notna(row["手续费"]) else None,
                })
            category_funds[symbol] = top
            print(f"  {symbol}: {len(top)} funds")
        except Exception as e:
            print(f"  {symbol} Error: {e}")
    return category_funds


def main():
    data = {}
    data["indices"] = fetch_indices()
    data["industry_boards"] = fetch_industry_boards()
    data["fund_flow"] = fetch_fund_flow()
    data["top_funds"] = fetch_top_funds()
    data["category_funds"] = fetch_category_funds()
    data["metadata"] = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "trading_date": data["top_funds"][0]["date"] if data["top_funds"] else datetime.now().strftime("%Y-%m-%d"),
    }

    # Write data.js
    js = "const FUND_DATA = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n"
    with open("data.js", "w", encoding="utf-8") as f:
        f.write(js)
    print(f"\ndata.js written ({len(js)/1024:.1f} KB)")


if __name__ == "__main__":
    main()
