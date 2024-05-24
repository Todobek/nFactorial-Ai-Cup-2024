from IPython.display import Markdown
import google.generativeai as genai
from config import GEMINI_API_KEY

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

sample_file = genai.upload_file(path="fridge.jpg",
                            display_name="fridge")

response = model.generate_content(["What ingredients do you see? Estimate the amount of each ingredient. IMPORTANT: Write straighforward list answer with no explanations", sample_file])
print(response.text)