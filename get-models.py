import google.generativeai as genai

API_KEY = "AIzaSyC-FKaJcE_LYP7MvugAWsRZ5cQkmXtwwmA"
genai.configure(api_key=API_KEY)

for model in genai.list_models():
    print(model.name)
