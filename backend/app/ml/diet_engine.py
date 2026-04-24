from app.config import get_settings
from groq import Groq
import json
import re

settings = get_settings()

# Configure Groq
groq_client = None
if settings.groq_api_key:
    groq_client = Groq(api_key=settings.groq_api_key.strip())

# Cancer type to dietary needs mapping (based on clinical oncology guidelines)
DIETARY_GUIDELINES = {
    "breast": {
        "avoid": ["alcohol", "processed meats", "high fat dairy"],
        "emphasize": ["cruciferous vegetables", "omega-3", "fiber"]
    },
    "lung": {
        "avoid": ["beta-carotene supplements"],
        "emphasize": ["antioxidants", "lean protein", "fruits"]
    },
    "colorectal": {
        "avoid": ["red meat", "alcohol", "processed foods"],
        "emphasize": ["fiber", "whole grains", "legumes"]
    },
    "prostate": {
        "avoid": ["high calcium supplements", "processed meats"],
        "emphasize": ["tomatoes (lycopene)", "green tea", "cruciferous vegetables"]
    },
    "default": {
        "avoid": ["processed foods", "excess sugar", "alcohol"],
        "emphasize": ["vegetables", "lean protein", "whole grains"]
    },
}


async def generate_diet_plan(user_profile: dict) -> dict:
    """Generate a personalized 7-day meal plan using Groq (Llama 3.1 70B)."""
    if not groq_client:
        return {"error": "Groq API key not configured. Please add GROQ_API_KEY to .env"}

    cancer_type = user_profile.get("cancer_type", "default").lower()
    guidelines = DIETARY_GUIDELINES.get(cancer_type, DIETARY_GUIDELINES["default"])

    prompt = f"""You are a clinical oncology dietitian. Create a detailed 7-day meal plan for:
- Cancer Type: {user_profile.get('cancer_type', 'unspecified')}
- Treatment Stage: {user_profile.get('stage', 'unspecified')}
- Fatigue Level: {user_profile.get('fatigue', 5)}/10
- Nausea Level: {user_profile.get('nausea', 3)}/10
- Appetite: {user_profile.get('appetite', 'moderate')}
- Food restrictions: {user_profile.get('restrictions', 'none')}

Dietary guidelines for {cancer_type} cancer:
- Emphasize: {', '.join(guidelines['emphasize'])}
- Avoid: {', '.join(guidelines['avoid'])}

For each day provide: breakfast, mid-morning snack, lunch, afternoon snack, dinner.
Format as JSON with this structure:
{{"day_1": {{"breakfast": {{"meal": "...", "calories": 300, "notes": "..."}}, "snack_am": {{...}}, "lunch": {{...}}, "snack_pm": {{...}}, "dinner": {{...}}}}, ...}}
Include only valid JSON, no explanation."""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
            temperature=0.3,
        )
        text = response.choices[0].message.content
        # Extract JSON from response
        json_match = re.search(r'\{[\s\S]+\}', text)
        if json_match:
            plan = json.loads(json_match.group())
        else:
            plan = {"error": "Invalid response format from AI"}
    except Exception as e:
        plan = {"error": f"Could not generate plan: {str(e)}"}

    return {"plan": plan, "guidelines": guidelines, "cancer_type": cancer_type}
