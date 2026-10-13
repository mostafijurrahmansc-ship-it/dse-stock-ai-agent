
import streamlit as st
import pandas as pd
import numpy as np
import feedparser
from urllib.parse import quote
from datetime import datetime, timezone

st.set_page_config(page_title="DSE Stock Analysis AI Agent", page_icon="📈", layout="wide")
st.title("📈 DSE Stock Analysis AI Agent")
st.caption("Online-ready prototype • DSE screening, price indicators, risk planning, and financial-news monitoring.")

tab_analysis, tab_news, tab_about = st.tabs(["📊 Stock analysis", "📰 News monitor", "ℹ️ About & data"])

with st.sidebar:
    st.header("Analysis settings")
    ticker = st.text_input("Ticker / company", value="GP")
    capital = st.number_input("Trading capital (BDT)", min_value=0.0, value=100000.0, step=10000.0)
    risk_pct = st.slider("Risk per trade (%)", min_value=0.25, max_value=3.0, value=1.0, step=0.25)
    rr = st.selectbox("Risk/reward target", ["1:1.5", "1:2", "1:3"], index=1)
    rr_mult = float(rr.split(":")[1])

def normalize_columns(df):
    mapping = {str(c).strip().lower(): c for c in df.columns}
    aliases = {"date":["date","datetime","timestamp"],"open":["open","opening"],"high":["high"],"low":["low"],"close":["close","ltp","price","last"],"volume":["volume","vol","trade volume"]}
    rename = {}
    for target, choices in aliases.items():
        found = next((mapping[x] for x in choices if x in mapping), None)
        if found is not None:
            rename[found] = target.title() if target == "date" else target.capitalize()
    return df.rename(columns=rename)

def add_indicators(df):
    df = df.copy()
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date", "Close"]).sort_values("Date").drop_duplicates("Date")
    df["SMA20"] = df["Close"].rolling(20).mean()
    df["SMA50"] = df["Close"].rolling(50).mean()
    delta = df["Close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    df["RSI14"] = 100 - (100 / (1 + rs))
    ema12 = df["Close"].ewm(span=12, adjust=False).mean()
    ema26 = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["AvgVol20"] = df["Volume"].rolling(20).mean()
    df["VolRatio"] = df["Volume"] / df["AvgVol20"].replace(0, np.nan)
    return df

def analyze(df):
    last = df.iloc[-1]
    score, reasons = 0, []
    if pd.notna(last.get("SMA20")):
        score += 1 if last["Close"] > last["SMA20"] else -1
        reasons.append("Close above SMA20." if last["Close"] > last["SMA20"] else "Close below SMA20.")
    if pd.notna(last.get("SMA50")):
        score += 1 if last["Close"] > last["SMA50"] else -1
        reasons.append("Close above SMA50." if last["Close"] > last["SMA50"] else "Close below SMA50.")
    if pd.notna(last.get("RSI14")):
        if 50 <= last["RSI14"] <= 70:
            score += 1; reasons.append("RSI is in the 50–70 momentum zone.")
        elif last["RSI14"] > 70:
            score -= 1; reasons.append("RSI is above 70; momentum may be overheated.")
        elif last["RSI14"] < 30:
            reasons.append("RSI is below 30; oversold does not guarantee a rebound.")
        else:
            reasons.append("RSI is below 50; momentum confirmation is absent.")
    if pd.notna(last.get("MACD")) and pd.notna(last.get("MACD_Signal")):
        score += 1 if last["MACD"] > last["MACD_Signal"] else -1
        reasons.append("MACD above signal line." if last["MACD"] > last["MACD_Signal"] else "MACD below signal line.")
    if pd.notna(last.get("VolRatio")):
        reasons.append(f"Volume is {last['VolRatio']:.2f}× the 20-day average.")
    label = "BULLISH SETUP" if score >= 2 else ("BEARISH / WEAK" if score <= -2 else "MIXED / WAIT")
    return label, score, reasons

with tab_analysis:
    st.subheader(f"{ticker.upper()} — technical analysis")
    uploaded = st.file_uploader("Upload historical price CSV", type=["csv"], key="price_csv")
    st.caption("Required columns: Date, Close, Volume. Open, High and Low are recommended. No live prices are implied.")
    if uploaded is None:
        st.info("Upload permitted historical OHLCV data to calculate indicators. The sample_prices.csv file in the project is synthetic demo data.")
    else:
        try:
            raw = normalize_columns(pd.read_csv(uploaded))
            missing = [c for c in ["Date","Close","Volume"] if c not in raw.columns]
            if missing:
                st.error("Missing required columns: " + ", ".join(missing))
            else:
                for col in ["Open","High","Low"]:
                    if col not in raw.columns: raw[col] = np.nan
                df = add_indicators(raw)
                if df.empty:
                    st.error("No valid rows. Check dates and prices.")
                else:
                    last = df.iloc[-1]
                    label, score, reasons = analyze(df)
                    a,b,c,d = st.columns(4)
                    a.metric("Latest close", f"৳{last['Close']:,.2f}", str(last["Date"].date()))
                    b.metric("RSI (14)", "—" if pd.isna(last["RSI14"]) else f"{last['RSI14']:.1f}")
                    c.metric("MACD", "—" if pd.isna(last["MACD"]) else f"{last['MACD']:.3f}")
                    d.metric("Volume ratio", "—" if pd.isna(last["VolRatio"]) else f"{last['VolRatio']:.2f}×")
                    st.markdown(f"### Signal: {label} | Rule score: {score:+d}")
                    st.caption("Transparent indicator rules, not an AI forecast or a guaranteed trade signal.")
                    with st.expander("Signal explanation", expanded=True):
                        for reason in reasons: st.write("• " + reason)
                    st.subheader("Close and moving averages")
                    st.line_chart(df.set_index("Date")[["Close","SMA20","SMA50"]])
                    st.subheader("RSI (14)")
                    st.line_chart(df.set_index("Date")[["RSI14"]])
                    st.subheader("Recent indicator data")
                    st.dataframe(df.tail(30).sort_values("Date", ascending=False), use_container_width=True)
                    st.subheader("Trade risk planner")
                    x,y,z = st.columns(3)
                    with x: entry = st.number_input("Planned entry (BDT)", min_value=0.01, value=float(last["Close"]), step=0.1)
                    with y: stop = st.number_input("Stop-loss (BDT)", min_value=0.0, value=max(0.01, round(float(last["Close"])*0.97,2)), step=0.1)
                    with z: target_override = st.number_input("Take-profit (0 = calculate)", min_value=0.0, value=0.0, step=0.1)
                    risk_share = entry-stop
                    if risk_share <= 0: st.error("For a long trade, stop-loss must be below entry.")
                    else:
                        risk_budget = capital*risk_pct/100
                        shares = int(risk_budget//risk_share)
                        target = target_override if target_override>0 else entry+risk_share*rr_mult
                        st.write(f"**Risk budget:** ৳{risk_budget:,.2f}  |  **Estimated quantity:** {shares:,} shares")
                        st.write(f"**Entry:** ৳{entry:,.2f} | **Stop:** ৳{stop:,.2f} | **Target:** ৳{target:,.2f} | **Reward/risk:** {(target-entry)/risk_share:.2f}:1")
                        st.caption("Adjust for lot size, liquidity, brokerage, slippage, price gaps and total position value.")
                    st.download_button("Download indicator CSV", df.to_csv(index=False).encode("utf-8"), file_name=f"{ticker.lower()}_analysis.csv", mime="text/csv")
        except Exception as e:
            st.error(f"Could not process CSV: {e}")

with tab_news:
    st.subheader("Financial news monitor")
    st.write("This tab queries RSS search results for the selected sources and displays headline links. It does not copy full articles.")
    query = st.text_input("Optional company/topic keyword", value="Bangladesh stock market")
    source_options = {
        "Investing.com": "site:investing.com/news OR site:investing.com/analysis",
        "StockAnalysis.com": "site:stockanalysis.com",
        "StockNow Bangladesh": "site:stocknow.com.bd OR site:news.stocknow.com.bd",
        "BRAC EPL Investments / Brokerage Research": "site:bracepl.com/investments OR site:bracepl.com/brokerage/research",
        "EBL Securities": "site:eblsecurities.com",
        "City Brokerage Limited": "site:citybrokerageltd.com",
        "ArthoSuchak": "site:arthosuchak.com",
        "DSE official": "site:dsebd.org OR site:dse.com.bd",
        "Reuters markets": "site:reuters.com/markets",
        "Economic Times markets": "site:economictimes.indiatimes.com/markets",
        "MarketWatch": "site:marketwatch.com",
        "Yahoo Finance": "site:finance.yahoo.com/news",
    }
    selected = st.multiselect("News sources", list(source_options.keys()), default=["Investing.com","StockAnalysis.com","StockNow Bangladesh","ArthoSuchak","DSE official"])
    max_items = st.slider("Maximum headlines per source", 3, 15, 7)
    if st.button("Fetch headlines", type="primary"):
        if not selected:
            st.warning("Select at least one source.")
        else:
            for source in selected:
                search_query = f'{source_options[source]} {query}'.strip()
                feed_url = "https://news.google.com/rss/search?q=" + quote(search_query) + "&hl=en-US&gl=US&ceid=US:en"
                with st.expander(source, expanded=True):
                    try:
                        feed = feedparser.parse(feed_url)
                        entries = feed.entries[:max_items]
                        if not entries:
                            st.write("No headlines returned for this query.")
                        for item in entries:
                            title = item.get("title","Untitled")
                            link = item.get("link","#")
                            published = item.get("published","Publication time unavailable")
                            st.markdown(f"**[{title}]({link})**")
                            st.caption(published)
                    except Exception as e:
                        st.warning(f"Could not load feed for {source}: {e}")
    st.caption("Headline availability depends on search indexing and source coverage. Verify important claims against the original article and official company disclosures.")

with tab_about:
    st.subheader("Sources and limitations")
    st.markdown("""
**Requested sources**
- [Investing.com](https://www.investing.com/) — official RSS feed information: [Investing.com RSS](https://www.investing.com/webmaster-tools/rss)
- [StockAnalysis.com](https://stockanalysis.com/) — used as a headline search link only in this prototype; its terms restrict automated/programmatic access.
- [StockNow Bangladesh](https://stocknow.com.bd/) and [StockNow News](https://news.stocknow.com.bd/)
- [BRAC EPL Investments](https://www.bracepl.com/investments/) and [BRAC EPL Brokerage Research](https://www.bracepl.com/brokerage/research/)
- [EBL Securities](https://www.eblsecurities.com/)
- [City Brokerage Limited](https://www.citybrokerageltd.com/)
- [ArthoSuchak](https://www.arthosuchak.com/)
- [Dhaka Stock Exchange](https://www.dsebd.org/)

**Data policy**
- This prototype uses Google News RSS search to find source-specific headlines rather than scraping full articles. Brokerage research sources include BRAC EPL Investments/Brokerage, EBL Securities and City Brokerage Limited; results depend on public indexing and availability.
- Investing.com offers RSS feeds; access terms and reuse conditions should be reviewed before production deployment.
- StockAnalysis.com terms prohibit automated access by bots/scripts except crawlers following robots.txt; this app does not scrape its pages.
- Price analysis only runs on the CSV you upload. No live DSE feed, AI sentiment scoring, or automated trading is connected yet.
- Do not treat news sentiment or technical indicators as a guaranteed prediction. Cross-check news and disclosures before making investment decisions.
""")
