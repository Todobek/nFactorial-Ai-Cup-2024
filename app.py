import streamlit as st
import requests
import base64
from io import BytesIO
from PIL import Image
import google.generativeai as genai
from openai import OpenAI
from config import OPENAI_API_KEY, BING_API_KEY, GEMINI_API_KEY

openai_api_key = OPENAI_API_KEY
client = OpenAI(api_key=openai_api_key)

bing_api_key = BING_API_KEY

genai.configure(api_key=GEMINI_API_KEY)
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}
model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config=generation_config,
)


photo_prompt = "What ingredients do you see? Estimate the amount of each ingredient. IMPORTANT: Write straighforward list answer with no explanations"

def analyze_fridge(image):
    image_path = "temp_fridge.jpg"
    image.save(image_path, format="JPEG")

    sample_file = genai.upload_file(path=image_path, display_name="fridge")
    response = model.generate_content([photo_prompt, sample_file])
    
    return response.text.strip()


def suggest_dish(ingredients, preferences):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": f"Suggest a dish based on the following ingredients: {ingredients}. Consider these preferences: {preferences}."}],
        max_tokens=1000
    )
    return response.choices[0].message.content.strip()

def get_dish_image(dish_name):
    headers = {"Ocp-Apim-Subscription-Key": bing_api_key}
    params = {"q": dish_name, "count": 1}
    response = requests.get("https://api.bing.microsoft.com/v7.0/images/search", headers=headers, params=params)
    image_url = response.json()["value"][0]["contentUrl"]
    return image_url


# Streamlit UI
st.title("FridgeAnalyzer")
st.write("Upload a photo of your fridge, and we'll suggest a dish for you to prepare.")

uploaded_file = st.file_uploader("Choose an image...", type="jpg")
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image.", use_column_width=True)

    ingredients = analyze_fridge(image)
    st.write("Ingredients detected:", ingredients)

    preferences = st.text_input("Any dietary preferences or restrictions?")
    if st.button("Suggest a Dish"):
        dish = suggest_dish(ingredients, preferences)
        st.write("Suggested Dish:", dish)

        dish_image_url = get_dish_image(dish)
        st.image(dish_image_url, caption=dish, use_column_width=True)