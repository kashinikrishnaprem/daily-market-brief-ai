import pandas as pd
from io import StringIO
from bs4 import BeautifulSoup
from newspaper import Article
import requests
import datetime
import os
from openai import OpenAI
import yfinance as yf
import feedparser
import gspread
import json
import re
from google.oauth2.service_account import Credentials

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------------- FETCH LIVE MARKET DATA ----------------
def fetch_market_data():
    try:
        nifty = yf.Ticker("^NSEI")
        banknifty = yf.Ticker("^NSEBANK")
        sensex = yf.Ticker("^BSESN")

        nifty_hist = nifty.history(period="5d")
        bank_hist = banknifty.history(period="5d")
        sensex_hist = sensex.history(period="5d")

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

        trade_date = nifty_hist.index[-1].strftime("%d %b %Y")
        max_move = max(abs(nifty_change), abs(bank_change), abs(sensex_change))

        if max_move < 0.5:
           regime = "Low Volatility Session"
        elif max_move < 1:
           regime = "Moderate Volatility Session"
        else:
           regime = "High Volatility Session"
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
# ---------------- FETCH FII / DII DATA FROM NSE ----------------

def fetch_fii_dii_data():

    try:

        session = requests.Session()

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.nseindia.com/reports/fii-dii"
        }

        # Get NSE cookies
        session.get(
            "https://www.nseindia.com",
            headers=headers,
            timeout=10
        )

        url = "https://www.nseindia.com/api/fiidiiTradeNse?csv=true"

        response = session.get(
            url,
            headers=headers,
            timeout=10
        )

        response.raise_for_status()

        print("===== NSE CSV =====")
        print(response.text[:1000])
        print("===================")

        return response.text

    except Exception as e:

        print("FII/DII Error:", e)

        return "FII/DII data unavailable."
# ---------------- FETCH LIVE NEWS ----------------

def extract_article_text(url):
    try:
        article = Article(url)
        article.download()
        article.parse()

        text = article.text

        # fallback if newspaper fails
        if not text:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            text = soup.get_text()

        return text[:3000]

    except Exception:
        return ""


def fetch_market_news():
    try:
        sources = [
            "https://news.google.com/rss/search?q=Nifty+Sensex+India+stock+market&hl=en-IN&gl=IN&ceid=IN:en",
            "https://news.google.com/rss/search?q=RBI+India+economy+markets&hl=en-IN&gl=IN&ceid=IN:en"
        ]

        all_articles = []

        for url in sources:
            feed = feedparser.parse(url)

            for entry in feed.entries[:6]:

                title = entry.title.strip()
                link = entry.link

                article_text = extract_article_text(link)

                # fallback if scraping fails
                if not article_text:
                    if hasattr(entry, "summary"):
                        article_text = entry.summary
                    elif hasattr(entry, "description"):
                        article_text = entry.description
                    else:
                        article_text = ""

                article_text = re.sub('<.*?>', '', article_text)

                article_block = f"""
TITLE: {title}

ARTICLE:
{article_text}
"""

                all_articles.append(article_block)

        # remove duplicates
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
def extract_fii_dii_from_news(news_text):

    try:

        prompt = f"""
From the following financial news text extract institutional flows.

Identify:
- FII net flow
- DII net flow

Return only this format:

FII Net Flow: ₹____ crore
DII Net Flow: ₹____ crore

If flows are not mentioned return:

FII Net Flow: Not reported
DII Net Flow: Not reported

NEWS TEXT:
{news_text}
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You extract financial data from financial news."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=120
        )

        return response.choices[0].message.content

    except Exception:

        return "FII Net Flow: Not reported\nDII Net Flow: Not reported"
# ---------------- LIVE DATA VARIABLES ----------------
market_data = fetch_market_data()
news_data = fetch_market_news()
global_data = fetch_global_data()
fii_dii_data = fetch_fii_dii_data()

if "unavailable" in fii_dii_data.lower():
    fii_dii_data = extract_fii_dii_from_news(news_data)

print("----- DEBUG FLOWS -----")
print(fii_dii_data)
print("-----------------------")

# ---------------- ANALYSIS INPUT ----------------
analysis_input = f"""
You are a professional equity market strategist writing a concise daily market brief.

Your goal is to explain **what happened, why it happened, and what investors should understand**.

Use the information below but you may **interpret relationships between market data and news logically**.

Avoid generic statements. Focus on **drivers and context**.

If FII/DII flows are not available, explicitly state that they were not reported and avoid inferring institutional behaviour.

DATE:
{today}

DOMESTIC MARKET DATA:
{market_data}

GLOBAL MARKET DATA:
{global_data}

INSTITUTIONAL FLOWS:
{fii_dii_data}

MARKET NEWS (full articles):
{news_data}


Write a professional research-style brief using this structure:

MARKET OVERVIEW
Summarize the overall session in India. Mention index performance and volatility.

KEY CATALYSTS
Identify the most likely drivers based on the news and data provided.

SECTOR / MARKET IMPACT
Explain which parts of the market appear most affected.

GLOBAL CONTEXT
Explain whether global markets may have influenced sentiment.

INSTITUTIONAL FLOWS
Explain how FII/DII flows align or diverge with the market move.

INVESTOR TAKEAWAY
Give a short interpretation of what the session signals for investors.


Style guidelines:

• Write like a professional research desk note  
• Avoid generic commentary  
• Be analytical but concise  
• Do NOT give predictions or buy/sell calls  
• Use clear financial language  
"""

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
    
# ---------------- RUN AI ANALYSIS ----------------

ai_output = generate_ai_brief(analysis_input)

print("===================================")
print("DAILY MARKET BRIEF – AI")
print("DATE:", today)
print("===================================")
print(ai_output)

# ---------------- WRITE TO GOOGLE SHEETS ----------------
def update_google_sheet(date, market_data, global_data, flows, news, brief):

    creds_json = os.getenv("GOOGLE_SERVICE_ACCOUNT")

    if not creds_json:
        raise Exception("GOOGLE_SERVICE_ACCOUNT secret not found.")

    creds_dict = json.loads(creds_json)

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)

    client = gspread.authorize(creds)

    sheet = client.open_by_key("1vSuZmhAYVgBhTz4nx9g_fZnmV2ulEUJwisjIWfoQK64").sheet1

    sheet.append_row(
        [date, market_data, global_data, flows, news, brief],
        value_input_option="RAW"
    )


# ---------------- EXECUTE GOOGLE SHEET UPDATE ----------------

update_google_sheet(
    today,
    market_data,
    global_data,
    fii_dii_data,
    news_data,
    ai_output
) 
