from flask import Flask, render_template, request
import os

app = Flask(__name__)

electives = ["Machine Learning", "Cyber Security", "Cloud Computing", "Data Science"]

# Enable this to simulate CPU load for testing
TEST_MODE = True  # Set to False to disable artificial CPU stress

@app.route('/')
def index():
    if TEST_MODE:
        for _ in range(10**6):
            _ = 3.14159 ** 2
    return render_template('index.html', electives=electives)

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form['name']
    elective = request.form['elective']

    if TEST_MODE:
        for _ in range(10**6):
            _ = 3.14159 ** 2

    return render_template('success.html', name=name, elective=elective)

if __name__ == '__main__':
    port = int(os.environ.get("FLASK_PORT", 5001))
    app.run(host='0.0.0.0', port=port)

