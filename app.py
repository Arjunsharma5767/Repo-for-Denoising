import os
import cv2
import numpy as np
from flask import Flask, request, send_from_directory, render_template_string, url_for, redirect
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESSED_FOLDER'] = 'processed'

# Create directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

# ========== CSS ==========
CSS_STYLE = """
body {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  margin: 0;
  padding: 0;
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
}
.container {
  background: white;
  width: 90%;
  max-width: 1000px;
  padding: 40px;
  border-radius: 15px;
  box-shadow: 0 15px 30px rgba(0,0,0,0.1);
  text-align: center;
}
h1 {
  color: #333;
  margin-bottom: 30px;
  font-weight: 700;
  font-size: 2.2rem;
}
.upload-area {
  border: 2px dashed #ccc;
  border-radius: 10px;
  padding: 30px;
  margin-bottom: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
}
.upload-area:hover {
  border-color: #4285f4;
  background-color: #f8f9fa;
}
.upload-icon {
  font-size: 48px;
  color: #4285f4;
  margin-bottom: 10px;
}
input[type="file"] {
  display: none;
}
.control-panel {
  margin: 20px 0;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 10px;
}
.button {
  padding: 12px 24px;
  background: #4285f4;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
  text-decoration: none;
  display: inline-block;
  margin: 10px 5px;
}
.button:hover {
  background: #3367d6;
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0,0,0,0.1);
}
.button.download {
  background: #34a853;
}
.button.download:hover {
  background: #2d9249;
}
.slider-container {
  margin: 20px 0;
  text-align: left;
}
.slider-container label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #555;
}
.slider {
  width: 100%;
  height: 5px;
  border-radius: 5px;
  -webkit-appearance: none;
  background: #ddd;
  outline: none;
}
.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #4285f4;
  cursor: pointer;
}
.image-container {
  margin-top: 30px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.image-wrapper {
  display: flex;
  justify-content: space-around;
  width: 100%;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.image-box {
  margin: 10px;
  text-align: center;
}
.image-box h3 {
  margin-bottom: 10px;
  color: #555;
}
img {
  max-width: 350px;
  max-height: 350px;
  border-radius: 8px;
  box-shadow: 0 5px 15px rgba(0,0,0,0.1);
  transition: transform 0.3s ease;
}
img:hover {
  transform: scale(1.03);
}
.back-link {
  display: block;
  margin-top: 20px;
  color: #4285f4;
  text-decoration: none;
  font-weight: 600;
}
.action-buttons {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-top: 20px;
}
.checkbox-container {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  margin: 15px 0;
  padding: 5px;
}
.checkbox-container input[type="checkbox"] {
  display: inline-block;
  width: 18px;
  height: 18px;
  margin-right: 10px;
  cursor: pointer;
}
.checkbox-container label {
  font-weight: 600;
  color: #555;
  cursor: pointer;
}
.twentytwenty-container {
  width: 100%;
  max-width: 600px;
  margin: 0 auto;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 0 15px rgba(0,0,0,0.1);
}
.twentytwenty-container img {
  width: 100%;
  display: block;
}
hr {
  margin: 40px 0; 
  border: 0; 
  border-top: 1px solid #ccc;
}
.comparison-slider {
  width: 100%;
  max-width: 700px;
  position: relative;
  overflow: hidden;
  border-radius: 8px;
  box-shadow: 0 5px 15px rgba(0,0,0,0.1);
  margin: 20px auto;
}
.radio-container {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  margin: 15px 0;
  padding: 10px;
  background: #f9f9f9;
  border-radius: 8px;
}
.radio-option {
  display: flex;
  align-items: center;
  margin: 8px 0;
}
.radio-option input[type="radio"] {
  margin-right: 10px;
}
.radio-option label {
  font-weight: 500;
  color: #555;
  cursor: pointer;
}
.method-description {
  margin-top: 5px;
  font-size: 0.9em;
  color: #777;
  text-align: left;
  padding-left: 25px;
}
"""

# ========== INDEX HTML ==========
INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Image Denoiser</title>
  <style>{{ css }}</style>
</head>
<body>
  <div class="container">
    <h1>🧹 Professional Image Denoiser</h1>
    <form id="upload-form" action="/" method="POST" enctype="multipart/form-data">
      <div class="upload-area" id="drop-area" onclick="document.getElementById('file-input').click()">
        <div class="upload-icon">📁</div>
        <p>Click to select or drag and drop an image</p>
      </div>
      <input type="file" id="file-input" name="image" accept="image/*" required>
      <div class="control-panel">
        <div class="slider-container">
          <label for="strength">Denoising Strength: <span id="strength-value">5</span></label>
          <input type="range" id="strength" name="strength" class="slider" min="1" max="10" value="5">
        </div>
        
        <div class="radio-container">
          <h3>Denoising Method:</h3>
          
          <div class="radio-option">
            <input type="radio" id="nlmeans" name="method" value="nlmeans" checked>
            <label for="nlmeans">Non-Local Means Denoising</label>
          </div>
          <p class="method-description">Best for natural images with fine details.</p>
          
          <div class="radio-option">
            <input type="radio" id="tvl1" name="method" value="tvl1">
            <label for="tvl1">TV-L1 Denoising</label>
          </div>
          <p class="method-description">Preserves edges while removing noise.</p>
          
          <div class="radio-option">
            <input type="radio" id="bilateral" name="method" value="bilateral">
            <label for="bilateral">Bilateral Filter</label>
          </div>
          <p class="method-description">Smooths while preserving edges and textures.</p>
        </div>
        
        <div class="checkbox-container">
          <input type="checkbox" id="grayscale" name="grayscale" value="yes">
          <label for="grayscale">Convert to Grayscale</label>
        </div>
        
        <button type="submit" class="button">Upload & Denoise</button>
      </div>
    </form>
  </div>
  <script>
    const strengthSlider = document.getElementById('strength');
    const strengthValue = document.getElementById('strength-value');
    strengthSlider.addEventListener('input', function() {
      strengthValue.textContent = this.value;
    });
    const dropArea = document.getElementById('drop-area');
    const fileInput = document.getElementById('file-input');
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
      dropArea.addEventListener(eventName, preventDefaults, false);
    });
    function preventDefaults(e) {
      e.preventDefault();
      e.stopPropagation();
    }
    ['dragenter', 'dragover'].forEach(eventName => {
      dropArea.addEventListener(eventName, highlight, false);
    });
    ['dragleave', 'drop'].forEach(eventName => {
      dropArea.addEventListener(eventName, unhighlight, false);
    });
    function highlight() {
      dropArea.style.borderColor = '#4285f4';
      dropArea.style.backgroundColor = '#f0f7ff';
    }
    function unhighlight() {
      dropArea.style.borderColor = '#ccc';
      dropArea.style.backgroundColor = 'transparent';
    }
    dropArea.addEventListener('drop', handleDrop, false);
    function handleDrop(e) {
      const dt = e.dataTransfer;
      const files = dt.files;
      if (files.length) {
        fileInput.files = files;
      }
    }
  </script>
</body>
</html>
"""

# ========== RESULT HTML ==========
RESULT_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Denoised Result</title>
    <meta charset="UTF-8">
    <style>{{ css }}</style>

    <!-- jQuery + twentytwenty -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/twentytwenty/1.0.0/css/twentytwenty.css" />
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery.event.move/2.0.0/jquery.event.move.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/twentytwenty/1.0.0/js/jquery.twentytwenty.js"></script>
</head>
<body>
    <div class="container">
        <h1>✨ Denoised Result</h1>
        
        <hr>

        <div class="image-container">
            <h3>🖼️ Side by Side View</h3>
            <div class="image-wrapper">
                <div class="image-box">
                    <h3>Original</h3>
                    <img src="{{ url_for('uploaded_file', filename=filename) }}" alt="Original Image">
                </div>
                <div class="image-box">
                    <h3>Denoised</h3>
                    <img src="{{ url_for('processed_file', filename=filename) }}" alt="Denoised Image">
                </div>
            </div>

            <div class="action-buttons">
                <a href="{{ url_for('download_file', filename=filename) }}" class="button download">⬇️ Download Denoised</a>
                <a href="{{ url_for('index') }}" class="button">⏪ Process Another Image</a>
            </div>
        </div>
    </div>

    <script>
      $(function(){
        $(".twentytwenty-container").twentytwenty({
          default_offset_pct: 0.5
        });
      });
    </script>
</body>
</html>
"""

# ========== IMAGE PROCESSING ==========
def denoise_image(input_path, output_path, strength=5, method="nlmeans", grayscale=False):
    """
    Apply denoising filters to the image
    
    Parameters:
    - input_path: Path to the input image
    - output_path: Path to save the processed image
    - strength: Denoising strength (1-10)
    - method: Denoising method to use (nlmeans, tvl1, bilateral)
    - grayscale: Whether to convert to grayscale
    """
    try:
        # Read the image
        image = cv2.imread(input_path)
        
        if image is None:
            raise ValueError(f"Failed to load image from {input_path}")
        
        # Convert to grayscale if requested
        if grayscale:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            # Convert back to BGR so we can save as color (but still grayscale)
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        
        # Scale strength parameter for different methods
        scaled_strength = strength / 10.0  # Convert to 0-1 range
        
        # Apply denoising based on selected method
        if method == "nlmeans":
            # Non-Local Means Denoising
            # Parameters: h (filter strength), templateWindowSize, searchWindowSize
            h_luminance = 3 + (10 * scaled_strength)  # Scale between 3-13 based on strength
            search_window = 21
            template_window = 7
            
            if len(image.shape) == 3:  # Color image
                denoised = cv2.fastNlMeansDenoisingColored(
                    image, 
                    None, 
                    h_luminance,  # Luminance component filter strength
                    h_luminance,  # Color component filter strength
                    template_window, 
                    search_window
                )
            else:  # Grayscale image
                denoised = cv2.fastNlMeansDenoising(
                    image, 
                    None, 
                    h_luminance,
                    template_window, 
                    search_window
                )
                
        elif method == "tvl1":
            # TV-L1 denoising (Total Variation L1)
            # Convert to float32 for processing
            img_float = image.astype(np.float32) / 255.0
            
            # Lambda parameter controls denoising strength
            lambda_val = 1.0 - (scaled_strength * 0.8)  # Invert so higher strength = more denoising
            
            # Apply TV-L1 to each channel separately
            if len(img_float.shape) == 3:
                denoised_channels = []
                for c in range(3):
                    denoised_channel = cv2.denoise_TVL1(img_float[:,:,c], lambda_val)
                    denoised_channels.append(denoised_channel)
                denoised_float = np.stack(denoised_channels, axis=2)
            else:
                denoised_float = cv2.denoise_TVL1(img_float, lambda_val)
            
            # Convert back to uint8
            denoised = np.clip(denoised_float * 255.0, 0, 255).astype(np.uint8)
            
        else:  # bilateral
            # Bilateral Filter
            # Parameters: d (diameter), sigmaColor, sigmaSpace
            d = 7  # Fixed diameter of pixel neighborhood
            sigma_color = 10 + (40 * scaled_strength)  # Range 10-50
            sigma_space = 10 + (40 * scaled_strength)  # Range 10-50
            
            denoised = cv2.bilateralFilter(image, d, sigma_color, sigma_space)
        
        # Save the processed image
        cv2.imwrite(output_path, denoised)
        
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        # If processing fails, copy the original to the output
        if os.path.exists(input_path):
            import shutil
            shutil.copy(input_path, output_path)

# ========== ROUTES ==========
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Check if image file was uploaded
        if 'image' not in request.files:
            return redirect(request.url)
        
        file = request.files['image']
        
        # If user doesn't select a file, browser submits an empty file
        if file.filename == '':
            return redirect(request.url)
        
        # Process the image if it exists
        if file:
            # Secure the filename to prevent directory traversal attacks
            filename = secure_filename(file.filename)
            
            # Define file paths
            input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            output_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
            
            # Save the uploaded file
            file.save(input_path)
            
            # Get image processing parameters
            strength = int(request.form.get('strength', 5))
            method = request.form.get('method', 'nlmeans')
            grayscale = request.form.get('grayscale') == 'yes'
            
            # Process the image
            denoise_image(input_path, output_path, strength, method, grayscale)
            
            # Render the result page
            return render_template_string(RESULT_HTML, filename=filename, css=CSS_STYLE)
    
    # Render the index page for GET requests
    return render_template_string(INDEX_HTML, css=CSS_STYLE)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve original uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/processed/<filename>')
def processed_file(filename):
    """Serve processed files"""
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename)

@app.route('/download/<filename>')
def download_file(filename):
    """Download processed files as attachments"""
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
