import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from typing import Literal
from dotenv import load_dotenv
import google.generativeai as genai

# Load .env
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("FATAL: GEMINI_API_KEY environment variable not set.")
    model = None
else:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(
        "gemini-2.5-flash-lite",
        generation_config={"response_mime_type": "application/json"}
    )

app = FastAPI(
    title="Smart Hydration & Nutrition Advisor",
    description="An API for personalized hydration and nutrition recommendations.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserProfile(BaseModel):
    age: int
    weight: float
    activity_level: str
    dietary_preferences: str
    disease: Literal["diabetes", "bp", "thyroid", "pcos", "heart", "anemia", "none"]
    gender: str

class Recommendations(BaseModel):
    daily_water_ml: float
    recommended_meals: list[str]
    reminders: list[str]

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse('favicon.ico')


@app.get("/")
async def get_index():
    return FileResponse('index.html')

@app.post("/calculate", response_model=Recommendations)
async def calculate_recommendations(profile: UserProfile):
    if not model:
        raise HTTPException(status_code=500, detail="Gemini API is not configured. Please set the GEMINI_API_KEY.")

    daily_water_ml = profile.weight * 35

    disease_instructions = {
        "diabetes": "low sugar, low glycemic index meals",
        "bp": "low sodium meals",
        "thyroid": "meals that support thyroid function, considering iodine levels",
        "pcos": "low carb, high-protein, insulin-friendly meals",
        "anemia": "iron-rich meals",
        "heart": "low saturated fat and low cholesterol meals",
        "none": "a balanced and healthy diet"
    }
    
    disease_prompt_part = disease_instructions.get(profile.disease, "a balanced diet")

    prompt = f"""
    As an expert nutritionist, create a personalized, one-day meal and reminder plan for the following user.
    The response MUST be unique and in JSON format with the specified schema.

    **JSON Schema:**
    {{
        "recommended_meals": ["meal_1", "meal_2", "meal_3"],
        "reminders": ["reminder_1", "reminder_2", "reminder_3"]
    }}

    **User Profile:**
    - Age: {profile.age}
    - Weight: {profile.weight} kg
    - Activity Level: {profile.activity_level}
    - Gender: {profile.gender}
    - Food Preference: {profile.dietary_preferences}
    - Health Goal: The user has '{profile.disease}', so the plan must follow '{disease_prompt_part}'.

    **Instructions:**
    1. Generate a list of 3 recommended meals (Breakfast, Lunch, Dinner).
    2. Generate a list of 3 simple, actionable health reminders.
    3. Return a JSON object with keys "recommended_meals" and "reminders".
    """

    try:
        response = await model.generate_content_async(prompt)
        ai_recommendations = json.loads(response.text)
        recommended_meals = ai_recommendations.get("recommended_meals", [])
        reminders = ai_recommendations.get("reminders", [])
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error parsing AI response: {e}")
        raise HTTPException(status_code=500, detail="Failed to parse AI recommendations.")
    except Exception as e:
        print(f"Unexpected AI error: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error from AI model: {e}")

    return Recommendations(
        daily_water_ml=daily_water_ml,
        recommended_meals=recommended_meals,
        reminders=reminders,
    )

if __name__ == "__main__":
    if not model:
        print("Exiting: Gemini API key not found.")
    else:
        uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
