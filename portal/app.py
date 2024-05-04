

from flask import Flask

app = Flask(__name__)
app.secret_key = "secret key"

# 350 MB limit for file uploads
app.config['MAX_CONTENT_LENGTH'] = 350 * 1024 * 1024

# mp4, mov extensions are allowed
app.config['UPLOAD_EXTENSIONS'] = ['.mp4', '.mov', '.MP4', '.MOV']

#upload_paths
app.config['UPLOAD_FOLDER'] = "/home/APSManagementSystem/uploads"


