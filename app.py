import os
import cv2
import numpy as np
from flask import Flask, request, send_from_directory, render_template_string, url_for, redirect
from werkzeug.utils import secure_filename
import time
from threading import Thread
from queue import Queue
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESSED_FOLDER'] = 'processed'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit uploads to 16MB
app.config['PROCESSING_QUEUE'] = Queue()

# Create directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

# Job status tracking
processing_jobs = {}

# CSS and HTML templates remain the same as in your original code
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
.status-label {
  padding: 8px 16px;
  border-radius: 4px;
  font-weight: bold;
  margin: 10px 0;
  display: inline-block;
}
.status-pending {
  background-color: #FFF8E1;
  color: #FFA000;
}
.status-processing {
  background-color: #E3F2FD;
  color: #1976D2;
}
.status-completed {
  background-color: #E8F5E9;
  color: #388E3C;
}
.status-failed {
  background-color: #FFEBEE;
  color: #D32F2F;
}
.spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border-left-color: #4285f4;
  animation: spin 1s linear infinite;
  display: inline-block;
  vertical-align: middle;
  margin-right: 10px;
}
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
.error-message {
  color: #D32F2F;
  background-color: #FFEBEE;
  padding: 15px;
  border-radius: 8px;
  margin: 20px 0;
  text-align: left;
  font-weight: 500;
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
    {% if error %}
    <div class="error-message">{{ error }}</div>
    {% endif %}
    <form id="upload-form" action="/" method="POST" enctype="multipart/form-data">
      <div class="upload-area" id="drop-area" onclick="document.getElementById('file-input').click()">
        <div class="upload-icon">📁</div>
        <p>Click to select or drag and drop an image (max 16MB)</p>
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
            <input type="radio" id="bilateral" name="method" value="bilateral">
            <label for="bilateral">Bilateral Filter</label>
          </div>
          <p class="method-description">Smooths while preserving edges and textures.</p>
          
          <div class="radio-option">
            <input type="radio" id="gaussian" name="method" value="gaussian">
            <label for="gaussian">Gaussian Filter</label>
          </div>
          <p class="method-description">Simple smoothing for uniform noise.</p>
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

# ========== PROCESSING HTML ==========
PROCESSING_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Processing Image</title>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="3;url={{ url_for('check_status', job_id=job_id) }}">
    <style>{{ css }}</style>
</head>
<body>
    <div class="container">
        <h1>🔄 Processing Your Image</h1>
        
        <div class="status-label status-processing">
            <div class="spinner"></div> Processing...
        </div>
        
        <p>Your image is being processed. This page will automatically refresh.</p>
        <p>Job ID: {{ job_id }}</p>
        
        <a href="{{ url_for('check_status', job_id=job_id) }}" class="button">Check Status Manually</a>
    </div>
    
    <script>
        // Refresh the page every 3 seconds to check status
        setTimeout(function() {
            window.location.href = "{{ url_for('check_status', job_id=job_id) }}";
        }, 3000);
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

# ========== ERROR HTML ==========
ERROR_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Processing Error</title>
    <meta charset="UTF-8">
    <style>{{ css }}</style>
</head>
<body>
    <div class="container">
        <h1>⚠️ Processing Error</h1>
        
        <div class="status-label status-failed">
            Failed
        </div>
        
        <div class="error-message">
            {{ error_message }}
        </div>
        
        <a href="{{ url_for('index') }}" class="button">Try Again</a>
    </div>
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
    - method: Denoising method to use (nlmeans, bilateral, gaussian)
    - grayscale: Whether to convert to grayscale
    """
    try:
        # Check if input file exists
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
            
        # Read the image
        image = cv2.imread(input_path)
        
        if image is None:
            raise ValueError(f"Failed to load image from {input_path}")
        
        # Resize large images to prevent timeouts
        max_dimension = 1500  # Maximum width or height
        height, width = image.shape[:2]
        
        # If image is too large, resize it
        if width > max_dimension or height > max_dimension:
            # Calculate scaling factor
            scale = min(max_dimension / width, max_dimension / height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            # Resize the image
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            logger.info(f"Resized image from {width}x{height} to {new_width}x{new_height}")
        
        # Convert to grayscale if requested
        if grayscale:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            # Convert back to BGR so we can save as color (but still grayscale)
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        
        # Scale strength parameter for different methods
        scaled_strength = strength / 10.0  # Convert to 0-1 range
        
        # Apply denoising based on selected method
        if method == "nlmeans":
            # Non-Local Means Denoising - Optimize parameters for better performance
            h_luminance = 3 + (10 * scaled_strength)  # Scale between 3-13 based on strength
            search_window = 15  # Reduced from 21 to improve performance
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
                
        elif method == "bilateral":
            # Bilateral Filter
            # Parameters: d (diameter), sigmaColor, sigmaSpace
            d = 7  # Fixed diameter of pixel neighborhood
            sigma_color = 10 + (40 * scaled_strength)  # Range 10-50
            sigma_space = 10 + (40 * scaled_strength)  # Range 10-50
            
            denoised = cv2.bilateralFilter(image, d, sigma_color, sigma_space)
            
        else:  # gaussian
            # Simple Gaussian blur
            # Parameters: ksize (kernel size), sigmaX
            kernel_size = int(3 + (scaled_strength * 4))  # Range from 3x3 to 7x7
            # Make sure kernel size is odd
            if kernel_size % 2 == 0:
                kernel_size += 1
                
            sigma = 0.3 + (scaled_strength * 1.7)  # Range from 0.3 to 2.0
            
            denoised = cv2.GaussianBlur(image, (kernel_size, kernel_size), sigma)
        
        # Save the processed image
        cv2.imwrite(output_path, denoised)
        return True, "Processing completed successfully"
        
    except Exception as e:
        error_msg = f"Error processing image: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

# Background worker thread to process images
def process_image_queue():
    while True:
        try:
            # Get a job from the queue
            job_id, input_path, output_path, params = app.config['PROCESSING_QUEUE'].get()
            
            # Update job status
            processing_jobs[job_id]['status'] = 'processing'
            
            # Process the image
            success, message = denoise_image(
                input_path, 
                output_path, 
                strength=params.get('strength', 5),
                method=params.get('method', 'nlmeans'),
                grayscale=params.get('grayscale', False)
            )
            
            # Update job status
            if success:
                processing_jobs[job_id]['status'] = 'completed'
            else:
                processing_jobs[job_id]['status'] = 'failed'
                processing_jobs[job_id]['error'] = message
            
            # Mark the task as done
            app.config['PROCESSING_QUEUE'].task_done()
            
        except Exception as e:
            logger.error(f"Worker thread error: {str(e)}")
            # If we get here, something went wrong with the worker itself
            if job_id in processing_jobs:
                processing_jobs[job_id]['status'] = 'failed'
                processing_jobs[job_id]['error'] = f"Worker thread error: {str(e)}"
            
            # Mark the task as done even if it failed
            app.config['PROCESSING_QUEUE'].task_done()

# Start the worker thread
worker_thread = Thread(target=process_image_queue, daemon=True)
worker_thread.start()

# ========== ROUTES ==========
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Check if image file was uploaded
        if 'image' not in request.files:
            return render_template_string(INDEX_HTML, css=CSS_STYLE, error="No file selected")
        
        file = request.files['image']
        
        # If user doesn't select a file, browser submits an empty file
        if file.filename == '':
            return render_template_string(INDEX_HTML, css=CSS_STYLE, error="No file selected")
        
        # Process the image if it exists
        if file:
            try:
                # Secure the filename to prevent directory traversal attacks
                filename = secure_filename(file.filename)
                
                # Check if the file is an image
                if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff')):
                    return render_template_string(INDEX_HTML, css=CSS_STYLE, 
                                                error="Unsupported file format. Please upload a PNG, JPG, JPEG, GIF, BMP, or TIFF image.")
                
                # Define file paths
                input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                output_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
                
                # Save the uploaded file
                file.save(input_path)
                
                # Get image processing parameters
                strength = int(request.form.get('strength', 5))
                method = request.form.get('method', 'nlmeans')
                grayscale = request.form.get('grayscale') == 'yes'
                
                # Create a job ID using timestamp
                job_id = f"{int(time.time())}_{filename}"
                
                # Add job to tracking dictionary
                processing_jobs[job_id] = {
                    'status': 'pending',
                    'filename': filename,
                    'created_at': time.time()
                }
                
                # Add job to processing queue
                app.config['PROCESSING_QUEUE'].put((
                    job_id,
                    input_path,
                    output_path,
                    {
                        'strength': strength,
                        'method': method,
                        'grayscale': grayscale
                    }
                ))
                
                # Redirect to processing page
                return render_template_string(PROCESSING_HTML, job_id=job_id, css=CSS_STYLE)
                
            except Exception as e:
                logger.error(f"Error handling upload: {str(e)}")
                return render_template_string(INDEX_HTML, css=CSS_STYLE, error=f"Error processing upload: {str(e)}")
    
    # Render the index page for GET requests
    return render_template_string(INDEX_HTML, css=CSS_STYLE)

@app.route('/status/<job_id>')
def check_status(job_id):
    if job_id not in processing_jobs:
        return render_template_string(ERROR_HTML, css=CSS_STYLE, 
                                     error_message="Job not found. It may have expired or been removed.")
    
    job = processing_jobs[job_id]
    
    # Check the job status
    if job['status'] == 'pending' or job['status'] == 'processing':
        # Still processing, show processing page
        return render_template_string(PROCESSING_HTML, job_id=job_id, css=CSS_STYLE)
    
    elif job['status'] == 'completed':
        # Processing completed, show result page
        filename = job['filename']
        return render_template_string(RESULT_HTML, filename=filename, css=CSS_STYLE)
    
    else:  # Failed
        # Processing failed, show error page
        error_message = job.get('error', 'Unknown error occurred during processing')
        return render_template_string(ERROR_HTML, css=CSS_STYLE, error_message=error_message)

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

# Add a simple health check endpoint
@app.route('/health')
def health_check():
    return "OK", 200

# Add a cleanup job to remove old processing jobs
def cleanup_old_jobs():
    current_time = time.time()
    to_remove = []
    
    for job_id, job in processing_jobs.items():
        # Remove jobs older than 1 hour
        if current_time - job['created_at'] > 3600:
            to_remove.append(job_id)
    
    for job_id in to_remove:
        processing_jobs.pop(job_id, None)

# Cleanup old jobs every 10 minutes
from apscheduler.schedulers.background import BackgroundScheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=cleanup_old_jobs, trigger="interval", minutes=10)
scheduler.start()

# Add a port binding that works with Render
port = int(os.environ.get("PORT", 5000))

if __name__ == '__main__':
    # Use Gunicorn for production
    app.run(host='0.0.0.0', port=port)
