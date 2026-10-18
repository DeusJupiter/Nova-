import os
from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import docx  # Zum Lesen von Word-Dateien

app = Flask(__name__)

app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)
)

chats_memory = {}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    chat_id = request.form.get("chat_id", "default_chat")
    user_message = request.form.get("message", "")
    
    file_content = ""
    if 'file' in request.files:
        uploaded_file = request.files['file']
        if uploaded_file.filename != '':
            filename = uploaded_file.filename.lower()
            try:
                if filename.endswith('.docx'):
                    # Word-Dokument auslesen
                    doc = docx.Document(uploaded_file)
                    file_text = "\n".join([para.text for para in doc.paragraphs])
                    file_content = f"\n\n[Inhalt der hochgeladenen Word-Datei '{uploaded_file.filename}':\n{file_text}\n]"
                else:
                    # Standard Textdateien / Code auslesen
                    file_text = uploaded_file.read().decode('utf-8', errors='ignore')
                    file_content = f"\n\n[Inhalt der hochgeladenen Datei '{uploaded_file.filename}':\n{file_text}\n]"
            except Exception as e:
                file_content = f"\n\n[Fehler beim Lesen der Datei: {str(e)}]"

    full_message = user_message + file_content

    if not full_message.strip():
        return jsonify({"response": "Bitte gib eine Nachricht ein oder lade eine Datei hoch."})

    if chat_id not in chats_memory:
        chats_memory[chat_id] = [
            {
                "role": "system",
                "content": (
                    "Du bist Nova, eine hochintelligente, freundliche und vielseitige KI-Assistentin. "
                    "Du hilfst dem Nutzer bei allen alltäglichen Fragen, beim Verfassen von Texten, "
                    "beim Analysieren von Dokumenten (auch Word/Textdateien) sowie bei komplexen Denk- und Programmieraufgaben. "
                    "Antworte stets präzise, hilfsbereit und gut strukturiert."
                )
            }
        ]

    chats_memory[chat_id].append({"role": "user", "content": full_message})

    try:
        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "http://localhost:5000",
                "X-Title": "Nova AI",
            },
            model="openrouter/auto:free",
            messages=chats_memory[chat_id]
        )

        bot_response = completion.choices[0].message.content
        chats_memory[chat_id].append({"role": "assistant", "content": bot_response})

    except Exception as e:
        bot_response = f"Fehler bei der KI-Anfrage: {str(e)}"

    return jsonify({"response": bot_response})

if __name__ == "__main__":
    app.run(debug=True)
