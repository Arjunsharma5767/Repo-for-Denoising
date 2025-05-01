import os
import cv2
import numpy as np
from flask import Flask, request, send_from_directory, render_template_string
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESSED_FOLDER'] = 'processed'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Image Sharpener</title>
  <style>{{ css }}</style>
</head>
<body>
  <div class="container">
    <h1>🔍 Image Sharpener</h1>
    <form method="POST" enctype="multipart/form-data">
      <input type="file" name="image" accept="image/*" required>
      <button type="submit">Upload & Sharpen</button>
    </form>
  </div>
</body>
</html>"""

RESULT_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Result</title>
  <style>{{ css }}</style>
</head>
<body>
  <div class="container">
    <h1>✨ Sharpened Image</h1>
    <img src="{{ url_for('processed_file', filename=filename) }}" alt="Sharpened Image">
    <br><a href="/">⏪ Back</a>
  </div>
</body>
</html>"""

CSS_STYLE = """body {
  font-family: Arial, sans-serif;
  background: #f5f5f5;
  text-align: center;
  padding-top: 50px;
}
.container {
  background: white;
  padding: 30px;
  border-radius: 10px;
  display: inline-block;
  box-shadow: 0 0 10px rgba(0,0,0,0.1);
}
input[type="file"] {
  margin: 10px 0;
}
button {
  padding: 10px 20px;
  background: #FF5733;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}
img {
  max-width: 80%;
  height: auto;
  margin-top: 20px;
  border-radius: 10px;
}"""

def sharpen_image(image_path, output_path):
    image = cv2.imread(image_path)
    kernel = np.array([[0, -1, 0],
                       [-1, 5,-1],
                       [0, -1, 0]])
    sharpened = cv2.filter2D(image, -1, kernel)
    cv2.imwrite(output_path, sharpened)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['image']
        if file:
            filename = secure_filename(file.filename)
            input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(input_path)

            output_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
            sharpen_image(input_path, output_path)

            return render_template_string(RESULT_HTML, filename=filename, css=CSS_STYLE)
    return render_template_string(INDEX_HTML, css=CSS_STYLE)

@app.route('/processed/<filename>')
def processed_file(filename):
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
