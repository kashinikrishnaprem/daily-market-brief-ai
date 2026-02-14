import datetime
import os
import requests

today = datetime.date.today().strftime("%d %b %Y")
market_data = """
NIFTY 50: -0.9%
BANK NIFTY: -1.2%
SENSEX: -0.8%
"""
news_data = """
1. Reuters: Indian shares fall as global markets weaken ahead of inflation data
   Lead: Indian equities declined modestly as investors turned cautious ahead of key global inflation data, tracking weakness in overseas markets.

2. RBI: Central bank commentary on inflation and rates
   Lead: The Reserve Bank of India reiterated its focus on inflation management while maintaining a data-dependent policy stance.
"""
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
def generate_ai_brief(prompt_text):
    api_url = "https://api-inference.huggingface.co/models/google/flan-t5-large"
    headers = {
        "Authorization": f"Bearer {os.getenv('HF_API_KEY')}"
    }

    payload = {
        "inputs": prompt_text,
       "parameters": {
    "max_new_tokens": 600
}
    }

    response = requests.post(api_url, headers=headers, json=payload)
    response.raise_for_status()

    result = response.json()
    return result[0]["generated_text"]
ai_output = generate_ai_brief(prompt)

print("===================================")
print("DAILY MARKET BRIEF – AI (FINAL)")
print("DATE:", today)
print("===================================")
print(ai_output)
