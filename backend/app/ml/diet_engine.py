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


RESTRICTION_RULES = {
    "vegetarian": ["beef", "chicken", "pork", "fish", "seafood", "gelatin"],
    "vegan": ["beef", "chicken", "pork", "fish", "seafood", "egg", "milk", "cheese", "yogurt", "butter", "honey"],
    "no dairy": ["milk", "cheese", "yogurt", "butter", "cream", "ghee", "whey"],
    "dairy free": ["milk", "cheese", "yogurt", "butter", "cream", "ghee", "whey"],
    "gluten free": ["wheat", "barley", "rye", "seitan", "regular pasta", "regular bread"],
    "nut free": ["almond", "walnut", "cashew", "pistachio", "pecan", "hazelnut", "peanut"],
    "low sodium": ["processed meats", "canned soup", "instant noodles", "salty snacks"],
}


def _normalize_restrictions(raw_restrictions):
    if raw_restrictions is None:
        return []
    if isinstance(raw_restrictions, str):
        return [item.strip().lower() for item in raw_restrictions.split(",") if item and item.strip()]
    if isinstance(raw_restrictions, list):
        return [str(item).strip().lower() for item in raw_restrictions if str(item).strip()]
    return [str(raw_restrictions).strip().lower()]


def _restriction_guardrails(restrictions):
    blocked = set()
    matched = []
    for restriction in restrictions:
        for rule, blocked_items in RESTRICTION_RULES.items():
            if rule in restriction:
                matched.append(rule)
                blocked.update(blocked_items)
    return sorted(set(matched)), sorted(blocked)


async def generate_diet_plan(user_profile: dict) -> dict:
    """Generate a personalized 7-day meal plan using Groq (Llama 3.1 70B)."""
    if not groq_client:
        return {"error": "Groq API key not configured. Please add GROQ_API_KEY to .env"}

    cancer_type = user_profile.get("cancer_type", "default").lower()
    guidelines = DIETARY_GUIDELINES.get(cancer_type, DIETARY_GUIDELINES["default"])
    restrictions = _normalize_restrictions(user_profile.get("restrictions_list") or user_profile.get("restrictions"))
    matched_rules, forbidden_items = _restriction_guardrails(restrictions)

    restriction_text = ", ".join(restrictions) if restrictions else "none"
    preferences_text = user_profile.get("preferences", "none")
    symptom_text = ", ".join(user_profile.get("symptoms", [])) if user_profile.get("symptoms") else "none"

    guardrails_block = "- No inferred hard blocks from built-in rule map."
    if forbidden_items:
        guardrails_block = f"- Never include these ingredients/items: {', '.join(forbidden_items)}"

    matched_rules_text = ", ".join(matched_rules) if matched_rules else "none"

    prompt = f"""You are a clinical oncology dietitian. Create a detailed 7-day meal plan for a patient with the following profile:
- Cancer Type: {user_profile.get('cancer_type', 'unspecified')}
- Treatment Stage: {user_profile.get('stage', 'unspecified')}
- Fatigue Level: {user_profile.get('fatigue', 5)}/10
- Nausea Level: {user_profile.get('nausea', 3)}/10
- Appetite: {user_profile.get('appetite', 'moderate')}
- Symptoms to consider: {symptom_text}
- Food preferences: {preferences_text}
- STRICT DIETARY RESTRICTIONS: {restriction_text}
- Matched restriction rules: {matched_rules_text}

NON-NEGOTIABLE SAFETY RULES:
1) You must STRICTLY ADHERE to all listed dietary restrictions.
2) Do NOT include any ingredient that violates those restrictions, even in small quantities.
3) If a requested meal conflicts with a restriction, replace it with a safe alternative.
4) Perform a final self-audit before returning JSON to ensure no meal violates restrictions.
{guardrails_block}

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
