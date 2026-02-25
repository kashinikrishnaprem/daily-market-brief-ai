import datetime
import os
from openai import OpenAI
import yfinance as yf

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

        nifty_change = ((nifty_hist["Close"].iloc[-1] - nifty_hist["Close"].iloc[-2]) / nifty_hist["Close"].iloc[-2]) * 100
        bank_change = ((bank_hist["Close"].iloc[-1] - bank_hist["Close"].iloc[-2]) / bank_hist["Close"].iloc[-2]) * 100
        sensex_change = ((sensex_hist["Close"].iloc[-1] - sensex_hist["Close"].iloc[-2]) / sensex_hist["Close"].iloc[-2]) * 100

        return f"""
NIFTY 50: {nifty_change:.2f}%
BANK NIFTY: {bank_change:.2f}%
SENSEX: {sensex_change:.2f}%
"""
    except Exception:
        return "Market data unavailable."
# ---------------- DATE ----------------
today = datetime.date.today().strftime("%d %b %Y")

# ---------------- LIVE DATA VARIABLES ----------------
market_data = fetch_market_data()

news_data = """
1. Reuters: Indian shares fall as global markets weaken ahead of inflation data
   Lead: Indian equities declined modestly as investors turned cautious ahead of key global inflation data.

2. RBI: Central bank commentary on inflation and rates
   Lead: The Reserve Bank of India reiterated its focus on inflation management while maintaining a data-dependent policy stance.
"""

# ---------------- ANALYSIS INPUT ----------------
analysis_input = f"""
You are a calm, data-driven equity market research analyst.

Using ONLY the information below, write a ONE-PAGE daily market brief.

DATE:
{today}

MARKET DATA:
{market_data}

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
