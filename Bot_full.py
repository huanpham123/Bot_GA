import os
from flask import Flask, render_template, request, session, jsonify
from openai import OpenAI

app = Flask(__name__, template_folder="templates")
app.secret_key = os.environ.get("SECRET_KEY", "default_secret_key")

# Lấy API key từ biến môi trường
API_KEY = os.environ["API_KEY"]
BASE_URL = "https://api.sree.shop/v1"

# Khởi tạo client OpenAI
client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)

# Cấu hình các mô hình chatbot
MODELS = {
    "gpt4o": {
         "name": "GPT-4o",
         "api_model": "gpt-4o",
         "extra_params": {}
    },
    "claude_35_sonnet": {
         "name": "Claude 3.5 Sonnet",
         "api_model": "claude-3-5-sonnet",
         "extra_params": {}
    },
    "deepseek_r1": {
         "name": "DeepSeek R1",
         "api_model": "deepseek-r1",
         "extra_params": {}
    },
    "deepseek_v3": {
         "name": "DeepSeek V3",
         "api_model": "deepseek-v3",
         "extra_params": {}
    },
    "llama3_turbo": {
         "name": "Llama 3 70B Turbo",
         "api_model": "Meta-Llama-3.3-70B-Instruct-Turbo",
         "extra_params": {}
    }
}

@app.route('/')
def index():
    if "model" not in session or session["model"] not in MODELS:
        session["model"] = "gpt4o"
    if "history" not in session:
        session["history"] = []
    return render_template("ghiam.html",
                           models=MODELS,
                           current_model=MODELS[session["model"]]["name"],
                           history=session["history"])

@app.route('/set_model', methods=['POST'])
def set_model():
    model = request.form.get("model")
    if model in MODELS:
        session["model"] = model
        session["history"] = []
        return jsonify({"status": "success", "model": model, "model_name": MODELS[model]["name"]})
    return jsonify({"status": "error", "message": "Model not found"}), 400

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get("message")
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    history = session.get("history", [])
    history.append({"role": "user", "content": user_message})

    selected_model_key = session.get("model", "gpt4o")
    model_info = MODELS.get(selected_model_key)
    if not model_info:
        return jsonify({"error": "Invalid model selected"}), 400

    try:
        response = client.chat.completions.create(
            model=model_info["api_model"],
            messages=history,
            **model_info.get("extra_params", {})
        )
        reply = response.choices[0].message.content
        history.append({"role": "assistant", "content": reply})
        session["history"] = history

        if selected_model_key in ["deepseek_r1", "deepseek_v3"]:
            if "Final Answer:" in reply:
                reasoning, final_answer = reply.split("Final Answer:", 1)
                reply_data = {"reasoning": reasoning.strip(), "final_answer": final_answer.strip()}
            else:
                reply_data = {"final_answer": reply}
        else:
            reply_data = {"final_answer": reply}

        return jsonify(reply_data)
    except Exception as e:
        return jsonify({"error": "API error", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
