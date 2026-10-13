
# DSE Stock Analysis AI Agent — Online prototype

## Deploy online (Streamlit Community Cloud)
1. Create a GitHub account if you do not have one.
2. Create a **private** repository named `dse-stock-ai-agent` (recommended while the project is a prototype).
3. Upload `app.py`, `requirements.txt`, `README.md`, and optionally `sample_prices.csv`.
4. Open https://share.streamlit.io/ and sign in with GitHub.
5. Choose **Create app**, select the repository, branch, and `app.py`.
6. Deploy. Streamlit will install packages from `requirements.txt` and provide an online URL.

Keep private credentials out of GitHub. This version needs no API keys. A public app may be accessible to anyone who has its URL; use Streamlit's current sharing/access controls if you need restricted access.

## Features
- CSV-based DSE price analysis: RSI14, MACD, SMA20/SMA50, relative volume
- Transparent bullish/mixed/bearish indicator screen
- Position sizing and risk/reward calculator
- News monitor querying source-specific Google News RSS results for Investing.com, StockAnalysis.com, StockNow, ArthoSuchak, DSE and selected global financial outlets
- Click-through headline links, not full article republication

## Limitations
- No live DSE price connection or automatic company financial statement extraction.
- No AI sentiment analysis yet; news results are headlines and links.
- The news search depends on Google News indexing and may omit stories.
- StockAnalysis.com terms restrict bots/scripts/scrapers; this app does not scrape that site.
- Check each source's terms before commercial reuse. Investing.com provides RSS feed information at https://www.investing.com/webmaster-tools/rss.
- Not financial advice; test any strategy with historical data, realistic costs, and slippage.

## Run locally
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## CSV format
Required columns: `Date`, `Close`, `Volume`
Recommended columns: `Open`, `High`, `Low`
