import datetime
import os
from openai import OpenAI

# ---------------- DATE ----------------
today = datetime.date.today().strftime("%d %b %Y")

# ---------------- MARKET DATA ----------------
market_data = """
NIFTY 50: -0.9%
BANK NIFTY: -1.2%
SENSEX: -0.8%
"""

# ---------------- NEWS DATA ----------------
news_data = """
1. Reuters: Indian shares fall as global markets weaken ahead of inflation data
   Lead: Indian equities declined modestly as investors turned cautious ahead of key global inflation data, tracking weakness in overseas markets.

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
