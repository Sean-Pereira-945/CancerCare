import httpx
import google.generativeai as genai
from app.config import get_settings

settings = get_settings()

# Configure Gemini
if settings.gemini_api_key:
    genai.configure(api_key=settings.gemini_api_key)

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


async def fetch_usda_foods(query: str) -> list:
    """Fetch nutritional data from USDA FoodData Central (free, no key needed)."""
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://api.nal.usda.gov/fdc/v1/foods/search",
            params={"query": query, "pageSize": 5, "dataType": "SR Legacy,Foundation Food"}
        )
        if r.status_code == 200:
            return r.json().get("foods", [])[:3]
    return []


async def generate_diet_plan(user_profile: dict) -> dict:
    """Generate a personalized 7-day meal plan using Gemini 1.5 Flash."""
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
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        import json, re
        text = response.text
        # Extract JSON from response
        json_match = re.search(r'\{[\s\S]+\}', text)
        if json_match:
            plan = json.loads(json_match.group())
        else:
            plan = {}
    except Exception as e:
        plan = {"error": f"Could not generate plan: {str(e)}"}

    return {"plan": plan, "guidelines": guidelines, "cancer_type": cancer_type}
