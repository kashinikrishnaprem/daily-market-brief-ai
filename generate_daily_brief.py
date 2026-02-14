# ==============================
# DAILY AI MARKET BRIEF GENERATOR
# ==============================

import datetime

# -------- STEP 1: DATE --------
today = datetime.date.today().strftime("%d %b %Y")

# -------- STEP 2: MARKET DATA (TEMP SAMPLE – WILL BE AUTOMATED NEXT) --------
market_data = """
NIFTY 50: -0.9%
BANK NIFTY: -1.2%
SENSEX: -0.8%
"""

# -------- STEP 3: VERIFIED NEWS (TEMP SAMPLE – FROM TRUSTED SOURCES) --------
news_data = """
1. Reuters: Indian shares fall as global markets weaken ahead of inflation data
   Lead: Indian equities declined modestly as investors turned cautious ahead of key global inflation data, tracking weakness in overseas markets.

2. RBI: Central bank commentary on inflation and rates
   Lead: The Reserve Bank of India reiterated its focus on inflation management while maintaining a data-dependent policy stance.
"""

# -------- STEP 4: ANALYST PROMPT (THIS IS THE BRAIN) --------
prompt = f"""
You are a professional equity market research analyst.

Using ONLY the verified data provided below, write a ONE-PAGE daily market brief.

DATE:
{today}

MARKET DATA:
{market_data}

VERIFIED NEWS:
{news_data}

Your brief must include the following sections:

1. Market Overview
Explain what happened in the market today using index data.
If the move is small, clearly say so.

2. Key Drivers
Identify the main factors influencing the market today.
Base this strictly on the news provided.
Avoid dramatic language.

3. Nature of the Move
State whether today’s movement appears sentiment-driven, data-driven, or policy-driven.
Explain briefly why.

4. Investor Interpretation
Explain how a long-term investor should interpret today’s action.
Do NOT give buy/sell calls.
Focus on mindset and risk awareness.

Rules:
- Be factual and data-driven
- Do not predict future market levels
- Do not speculate
- If headlines appear exaggerated, rely on index data to moderate tone
- Use calm, professional language

End with a short section titled: "Investor Takeaway".
"""

# -------- STEP 5: OUTPUT (FOR NOW, JUST PRINT) --------
print("===================================")
print("DAILY MARKET BRIEF – AI (DRAFT)")
print("DATE:", today)
print("===================================")
print(prompt)
