import requests
import pandas as pd
from io import StringIO
import datetime
import os
from openai import OpenAI
import yfinance as yf
import feedparser

# ---------------- FETCH LIVE MARKET DATA ----------------
def fetch_market_data():
    try:
        nifty = yf.Ticker("^NSEI")
        banknifty = yf.Ticker("^NSEBANK")
        sensex = yf.Ticker("^BSESN")

        nifty_hist = nifty.history(period="5d")
        bank_hist = banknifty.history(period="5d")
        sensex_hist = sensex.history(period="5d")

        # 🔒 LENGTH CHECK (CRITICAL FOR STABILITY)
        if len(nifty_hist) < 2 or len(bank_hist) < 2 or len(sensex_hist) < 2:
            return "Market data unavailable."

        nifty_close = nifty_hist["Close"].iloc[-1]
        bank_close = bank_hist["Close"].iloc[-1]
        sensex_close = sensex_hist["Close"].iloc[-1]

        nifty_prev = nifty_hist["Close"].iloc[-2]
        bank_prev = bank_hist["Close"].iloc[-2]
        sensex_prev = sensex_hist["Close"].iloc[-2]

        nifty_points = nifty_close - nifty_prev
        bank_points = bank_close - bank_prev
        sensex_points = sensex_close - sensex_prev

        nifty_change = (nifty_points / nifty_prev) * 100
        bank_change = (bank_points / bank_prev) * 100
        sensex_change = (sensex_points / sensex_prev) * 100
        # ---- Trade Date ----
        trade_date = nifty_hist.index[-1].strftime("%d %b %Y")

        # ---- Volatility Regime ----
        max_move = max(abs(nifty_change), abs(bank_change), abs(sensex_change))

        if max_move < 0.50:
            regime = "Low Volatility Session"
        elif max_move < 1.00:
            regime = "Moderate Volatility Session"
        else:
            regime = "Elevated Volatility Session"

        return f"""
Trade Date: {trade_date}
Session Type: {regime}

NIFTY 50: {nifty_close:.2f} ({nifty_points:+.2f}, {nifty_change:.2f}%)
BANK NIFTY: {bank_close:.2f} ({bank_points:+.2f}, {bank_change:.2f}%)
SENSEX: {sensex_close:.2f} ({sensex_points:+.2f}, {sensex_change:.2f}%)
"""

    except Exception:
        return "Market data unavailable."
# ---------------- FETCH GLOBAL MARKET DATA ----------------
def fetch_global_data():
    try:
        sp500 = yf.Ticker("^GSPC")
        nasdaq = yf.Ticker("^IXIC")
        dow = yf.Ticker("^DJI")
        usd_inr = yf.Ticker("INR=X")
        brent = yf.Ticker("BZ=F")

        sp_hist = sp500.history(period="5d")
        nas_hist = nasdaq.history(period="5d")
        dow_hist = dow.history(period="5d")
        usd_hist = usd_inr.history(period="5d")
        brent_hist = brent.history(period="5d")

        if any(len(hist) < 2 for hist in [sp_hist, nas_hist, dow_hist, usd_hist, brent_hist]):
            return "Global data unavailable."

        def calc(hist):
            close = hist["Close"].iloc[-1]
            prev = hist["Close"].iloc[-2]
            points = close - prev
            pct = (points / prev) * 100
            return close, points, pct

        sp_close, sp_pts, sp_pct = calc(sp_hist)
        nas_close, nas_pts, nas_pct = calc(nas_hist)
        dow_close, dow_pts, dow_pct = calc(dow_hist)
        usd_close, usd_pts, usd_pct = calc(usd_hist)
        brent_close, brent_pts, brent_pct = calc(brent_hist)

        return f"""
S&P 500: {sp_close:.2f} ({sp_pts:+.2f}, {sp_pct:.2f}%)
NASDAQ: {nas_close:.2f} ({nas_pts:+.2f}, {nas_pct:.2f}%)
DOW JONES: {dow_close:.2f} ({dow_pts:+.2f}, {dow_pct:.2f}%)
USD/INR: {usd_close:.2f} ({usd_pts:+.2f}, {usd_pct:.2f}%)
BRENT CRUDE: {brent_close:.2f} ({brent_pts:+.2f}, {brent_pct:.2f}%)
"""

    except Exception:
        return "Global data unavailable."
# ---------------- FETCH FII / DII DATA (HYBRID SYSTEM) ----------------
def fetch_fii_dii_data():
    today_str = datetime.date.today().strftime("%d-%b-%Y")
    archive_date = datetime.date.today().strftime("%d%m%Y")

    # =========================
    # PRIMARY: NSE ARCHIVE CSV
    # =========================
    try:
        url = f"https://archives.nseindia.com/content/fo/fo_fii_stats_{archive_date}.csv"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            df = pd.read_csv(StringIO(response.text))

            # Look for net total row
            df.columns = [col.strip() for col in df.columns]

            net_row = df[df.iloc[:,0].str.contains("Net", na=False)]

            if not net_row.empty:
                fii_net = net_row.iloc[0][1]
                dii_net = net_row.iloc[0][2]

                return f"""
Flow Date: {today_str}
Source: NSE Archive

FII Net Flow: ₹{fii_net} crore
DII Net Flow: ₹{dii_net} crore
Flow Status: Archive Data
"""

    except Exception:
        pass

    # =========================
    # FALLBACK: MONEYCONTROL
    # =========================
    try:
        mc_url = "https://www.moneycontrol.com/stocks/marketstats/fii_dii_activity/index.php"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(mc_url, headers=headers, timeout=10)

        tables = pd.read_html(response.text)

        if tables:
            df = tables[0]
            latest = df.iloc[0]

            date = latest[0]
            fii_net = latest[3]
            dii_net = latest[5]

            return f"""
Flow Date: {date}
Source: Moneycontrol

FII Net Flow: ₹{fii_net} crore
DII Net Flow: ₹{dii_net} crore
Flow Status: Fallback Source
"""

    except Exception:
        pass

    # =========================
    # FINAL FALLBACK
    # =========================
    return "Institutional flow data could not be retrieved from available sources."
# ---------------- FETCH LIVE NEWS ----------------
# ---------------- FETCH MULTI-SOURCE NEWS WITH SUMMARIES ----------------
def fetch_market_news():
    try:
        sources = [
            "https://finance.yahoo.com/rss/topstories",
            "https://feeds.reuters.com/reuters/businessNews",
            "https://news.google.com/rss/search?q=India+stock+market&hl=en-IN&gl=IN&ceid=IN:en"
        ]

        all_articles = []

        for url in sources:
            feed = feedparser.parse(url)

            for entry in feed.entries[:4]:
                title = entry.title.strip()

                summary = ""
                if hasattr(entry, "summary"):
                    summary = entry.summary
                elif hasattr(entry, "description"):
                    summary = entry.description

                import re
                summary = re.sub('<.*?>', '', summary)
                summary = summary[:400]

                article_block = f"""TITLE: {title}
SUMMARY: {summary}
"""
                all_articles.append(article_block)

        # Deduplicate by title
        unique_articles = []
        seen_titles = set()

        for article in all_articles:
            title_line = article.split("TITLE: ")[1].split("\n")[0]
            if title_line not in seen_titles:
                seen_titles.add(title_line)
                unique_articles.append(article)

        if not unique_articles:
            return "No relevant market news available."

        return "\n\n".join(unique_articles[:6])

    except Exception:
        return "News data unavailable."
# ---------------- DATE ----------------
today = datetime.date.today().strftime("%d %b %Y")

# ---------------- LIVE DATA VARIABLES ----------------
market_data = fetch_market_data()
news_data = fetch_market_news()
global_data = fetch_global_data()
fii_dii_data = fetch_fii_dii_data()

print("----- DEBUG FLOWS -----")
print(fii_dii_data)
print("-----------------------")

# ---------------- ANALYSIS INPUT ----------------
analysis_input = f"""

You are a calm, data-driven equity market research analyst.

Data hierarchy priority:
1. Domestic index movement
2. Institutional flows
3. Explicitly linked domestic news
4. Global context (background only unless directly linked)

Using STRICTLY AND ONLY the information explicitly written below,
do NOT introduce any external facts, numbers, valuations,
or assumptions not directly stated in the data provided.

If information is missing, state that clearly instead of inferring.

If referencing global markets, clearly distinguish between correlation and direct causation.
Do not over-emphasize global cues unless explicitly linked in the provided news summaries.

If FII and DII flows are available, mention whether flows align or diverge from index direction.
Do not speculate on reasons beyond the provided data.

If global indices and domestic indices move in opposite directions,
explicitly highlight the divergence without implying causation.

Global market movements must NOT be described as drivers unless the news summaries explicitly link them to Indian markets.
If no explicit linkage exists in the news text, describe global moves as background context only.

If no domestic news explicitly connects global markets to Indian indices,
classify global movements strictly as background context.

If domestic index movement is below 0.50%, describe it as marginal or modest and avoid directional adjectives like strong, sharp, or rally.

Institutional flows must be explicitly addressed.
If FII net flow and index direction align, state alignment.
If they diverge, explicitly highlight divergence.
Do not ignore institutional flow data.

If FII net flow is positive and index is positive, mention alignment.
If FII net flow is negative while index is positive (or vice versa), highlight divergence.

If institutional flow data contains a Source field, mention the source once in Market Overview.
If flow data could not be retrieved, clearly state that it was unavailable.

DATE:
{today}

DOMESTIC MARKET DATA:
{market_data}

GLOBAL MARKET CONTEXT:
{global_data}

INSTITUTIONAL FLOWS:
{fii_dii_data}

KEY NEWS:
{news_data}

Structure your response as:

1. Market Overview
2. Key Drivers
3. Nature of the Move (sentiment / data / policy driven)
4. Investor Interpretation

Rules:
- No predictions
- No buy/sell calls
- Moderate tone
- Let data override dramatic headlines

End with a short section titled: "Investor Takeaway".
"""

# ---------------- OPENAI CLIENT ----------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_ai_brief(text):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a professional equity market analyst."},
            {"role": "user", "content": text}
        ],
        temperature=0.25,
        max_tokens=650
    )
    return response.choices[0].message.content

# ---------------- RUN ONCE ----------------
ai_output = generate_ai_brief(analysis_input)

print("===================================")
print("DAILY MARKET BRIEF – AI")
print("DATE:", today)
print("===================================")
print(ai_output)
