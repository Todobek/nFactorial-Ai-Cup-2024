import streamlit as st
import requests
from io import BytesIO
from PIL import Image
import google.generativeai as genai
import os

BING_API_KEY = os.getenv('BING_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not all([BING_API_KEY, GEMINI_API_KEY]):
    raise ValueError("One or more API keys are not set in environment variables")

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

photo_prompt = "What ingredients do you see? Estimate the amount of each ingredient. IMPORTANT: Write straightforward list answer with no explanations"
dish_prompt = "Suggest a dish based on the following ingredients: {ingredients}. Consider these preferences: {preferences}. IMPORTANT: suggest dish only, no recipe and no additional comments"
recipe_prompt = "Suggest a recipe for the {dish}. I have following ingredients: {ingredients} and these preferences: {preferences}. IMPORTANT: suggest recipe and its details only; do not write your opinion or speculations. VERY IMPORTANT: all the text should be in the same font size."

def analyze_fridge(image):
    image_path = "temp_fridge.jpg"
    if image.format == "JPEG":
        image.save(image_path, format="JPEG")
    else:
        image.save(image_path, format="PNG")

    sample_file = genai.upload_file(path=image_path, display_name="fridge")
    response = model.generate_content([photo_prompt, sample_file])
    
    return response.text.strip()

def suggest_dish(ingredients, preferences):
    prompt = dish_prompt.format(ingredients=ingredients, preferences=preferences)
    response = model.generate_content([prompt])
    return response.text.strip()

def suggest_recipe(ingredients, preferences, dish):
    prompt = recipe_prompt.format(dish= dish, ingredients=ingredients, preferences=preferences)
    response = model.generate_content([prompt])
    return response.text.strip()

def get_dish_image(dish_name):
    headers = {"Ocp-Apim-Subscription-Key": bing_api_key}
    params = {"q": dish_name, "count": 1}
    response = requests.get("https://api.bing.microsoft.com/v7.0/images/search", headers=headers, params=params)
    response_json = response.json()

    if "value" in response_json and len(response_json["value"]) > 0:
        image_url = response_json["value"][0]["contentUrl"]
        return image_url
    else:
        return None

# Initialize session state
if 'page' not in st.session_state:
    st.session_state['page'] = 'home'
if 'ingredients' not in st.session_state:
    st.session_state['ingredients'] = ''
if 'preferences' not in st.session_state:
    st.session_state['preferences'] = {}
if 'dish' not in st.session_state:
    st.session_state['dish'] = ''
if 'recipe' not in st.session_state:
    st.session_state['recipe'] = ''
if 'dish_image' not in st.session_state:
    st.session_state['dish_image'] = ''

def go_to_page(page):
    st.session_state['page'] = page
    st.experimental_rerun()

def title_page():
    st.title("🍳 letAIcook: Your Personal AI Chef!")
    st.subheader("Discover Delicious Recipes Based on What's in Your Fridge")
    st.write("""
    **Welcome to letAIcook!** 
    
    Upload photos of your fridge, and our AI will help you identify the ingredients you have. 
    Based on your dietary preferences, we'll suggest mouth-watering dishes and provide you with detailed recipes.
    
    Ready to turn your fridge into a feast? Click the button below to get started!
    """)
    if st.button("Start Your Culinary Journey", type="primary"):
        go_to_page('upload')


def upload_page():
    st.title("Let’s see what you got in your fridge")
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "png"])
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image.", use_column_width=True)
        if st.button("Next"):
            st.session_state['ingredients'] = analyze_fridge(image)
            go_to_page('preferences')

def preferences_page():
    st.title("Ingredients and preferences")
    container = st.container(border=True)
    container.write("Ingredients:")
    container.write(st.session_state['ingredients'])
    with st.form(key='preferences_form'):
        add_ingredients = st.text_input("Did we miss something?")
        diet = st.radio("Diet preference", ['Vegan', 'Vegetarian', 'Meat Eater', 'No preference'])
        meal_type = st.radio("Meal type", ['Breakfast', 'Lunch', 'Dinner', 'Snack'])
        calories = st.slider("Number of calories", 100, 2000, 500, 50)
        dietary_restriction = st.radio("Dietary restrictions", ['Halal', 'Kosher', 'No preference'])
        hungry = st.checkbox("Hungry?")
        additions = st.text_input("Any additions?")
        submit_button = st.form_submit_button(label='Get results')

    if submit_button:
        st.session_state['preferences'] = {
            'diet': diet,
            'meal_type': meal_type,
            'calories': calories,
            'dietary_restriction': dietary_restriction,
            'hungry': hungry,
            'additions': additions
        }
        st.session_state['ingredients'] = st.session_state['ingredients'] + " " + add_ingredients
        go_to_page('loading')

def loading_page():
    st.title("Please wait")
    st.write("Processing your request...")
    ingredients = st.session_state['ingredients']
    preferences = st.session_state['preferences']
    preferences_str = ', '.join([f"{key}: {value}" for key, value in preferences.items()])
    dish = suggest_dish(ingredients, preferences_str)
    recipe = suggest_recipe(ingredients, preferences_str, dish)
    st.session_state['dish'] = dish
    st.session_state['recipe'] = recipe
    st.session_state['dish_image'] = get_dish_image(dish)
    go_to_page('results')

def results_page():
    st.title("Suggested Dish")
    st.write("Suggested Dish:", st.session_state['dish'])
    st.write(st.session_state['recipe'])
    if st.session_state['dish_image']:
        st.image(st.session_state['dish_image'], caption=st.session_state['dish'], use_column_width=True)
    else:
        st.write("Sorry, no image found for the suggested dish.")

    col1, col2, col3 = st.columns(3, gap="large")
    with col1:
        if st.button("Homepage"):
            go_to_page('home')
    with col2:
        if st.button("Change preferences", type="primary"):
            go_to_page('preferences')
    with col3:
        if st.button("Get another recipe"):
            go_to_page('loading')


# Page routing
if st.session_state['page'] == 'home':
    title_page()
elif st.session_state['page'] == 'upload':
    upload_page()
elif st.session_state['page'] == 'preferences':
    preferences_page()
elif st.session_state['page'] == 'loading':
    loading_page()
elif st.session_state['page'] == 'results':
    results_page()