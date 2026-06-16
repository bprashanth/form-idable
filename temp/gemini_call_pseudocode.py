import google.generativeai as genai

# 1. Configure your API key
genai.configure(api_key="YOUR_GEMINI_API_KEY")

# 2. Upload the file to the managed staging bucket
print("Uploading datasheet...")
input_file = genai.upload_file(path="input.pdf", mime_type="application/pdf")
print(f"File uploaded successfully. Internal Name: {input_file.name}")

# 3. Pass the file object directly into the prompt request
model = genai.GenerativeModel(model_name="gemini-1.5-flash") # Or gemini-2.5-flash or gemini-3.5-flash

response = model.generate_content([
    input_file,
    "Analyze this ecology datasheet and output the data in a clean structured format."
])

print(response.text)
