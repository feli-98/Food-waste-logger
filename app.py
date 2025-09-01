from flask import Flask, render_template, request
from flask_mysqldb import MySQL
import openai
import os

app = Flask(__name__)

# MySQL config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'   # change if needed
app.config['MYSQL_PASSWORD'] = ''   # your MySQL password
app.config['MYSQL_DB'] = 'foodlogger'
mysql = MySQL(app)

# OpenAI config
openai.api_key = os.getenv("OPENAI_API_KEY")  # set in env

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/submit', methods=['POST'])
def submit():
    ingredient = request.form['ingredient']
    quantity = request.form['quantity']

    # Build prompt for AI
    prompt = f"""
    You are a food waste assistant. A user has leftover {quantity} of {ingredient}.
    Suggest 3 creative, affordable meal ideas to reuse it.
    Add 1 simple food safety tip.
    Keep answers short, Kenyan context.
    """

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200
    )

    ai_suggestions = response['choices'][0]['message']['content']

    # Save to DB
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO logs (ingredient, quantity, ai_suggestions) VALUES (%s, %s, %s)",
                (ingredient, quantity, ai_suggestions))
    mysql.connection.commit()
    cur.close()

    # Render result page (no need to pass suggestions anymore)
    return render_template("result.html", ingredient=ingredient, quantity=quantity)

@app.route('/history')
def history():
    cur = mysql.connection.cursor()
    cur.execute("SELECT ingredient, quantity, ai_suggestions, created_at FROM logs ORDER BY created_at DESC LIMIT 10")
    raw_data = cur.fetchall()
    cur.close()

    # Convert raw tuples into dictionaries that match your HTML template
    history_data = []
    for row in raw_data:
        entry = {
            'date': row[3].strftime('%Y-%m-%d %H:%M'),  # Format timestamp
            'item': row[0],
            'quantity': row[1],
            'reason': row[2]  # This is the AI suggestion
        }
        history_data.append(entry)

    return render_template("history.html", history=history_data)

if __name__ == '__main__':
    app.run(debug=True)