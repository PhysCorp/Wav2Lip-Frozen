from flask import Flask, request, jsonify, send_file
import os
import time
import random
import threading
import subprocess
import logging
from waitress import serve

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('waitress')
logger.setLevel(logging.DEBUG)

# Determine main program directory
maindirectory = os.path.dirname(os.path.abspath(__file__)) # The absolute path to this file

# Setup the Flask app
app = Flask(__name__)

# Init queue var
queue = []

# Set global bool to define whether an item in queue is processing
processing = False

def run_task(task):
    global processing
    processing = True
    # Run the task
    checkpoint_path = os.path.join(maindirectory, 'checkpoints', 'wav2lip_gan.pth')
    input_video_path = os.path.join(maindirectory, '..', 'tasks', task['task_id'], 'input_video.mp4')
    input_audio_path = os.path.join(maindirectory, '..', 'tasks', task['task_id'], 'input_audio.wav')
    # Convert the paths to strings
    checkpoint_path = str(checkpoint_path)
    input_video_path = str(input_video_path)
    input_audio_path = str(input_audio_path)
    temp_command = ["python3", "inference.py", "--checkpoint_path", checkpoint_path, "--face", input_video_path, "--audio", input_audio_path, "--pads", "0", "20", "0", "0"]
    print(f"[INFO] Running command: {' '.join(temp_command)}")
    process = subprocess.Popen(temp_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    with open(os.path.join(maindirectory, '..', 'tasks', task['task_id'], 'status.txt'), 'w') as status_file:
        # Write the command to the status file
        # status_file.write(f"Command: {' '.join(temp_command)}\n")
        while process.poll() is None:
            lines = []
            for line in iter(process.stdout.readline, b''):
                output = line.decode().strip()
                lines.append(output)
                if len(lines) > 10:
                    lines.pop(0)
                status_file.write(output + '\n')
                status_file.flush()
            time.sleep(10)  # Update status every 10 seconds
        # Write the last 10 lines to the status file
        for line in lines:
            status_file.write(line + '\n')
    # Update the status.txt file with the final status
    with open(os.path.join(maindirectory, '..', 'tasks', task['task_id'], 'status.txt'), 'a') as status_file:
        status_file.write(':::Completed:::\n')
    # Set processing to False
    processing = False

def check_queue():
    global processing
    max_attempts = 5
    current_attempt = 0
    while True:
        if queue:
            # Check if the first item in the queue is processing
            if processing:
                # Wait for the item to finish
                if current_attempt < max_attempts:
                    current_attempt += 1
                    time.sleep(60)
                    continue
                else:
                    current_attempt = 0
                    # Attempt to kill old thread
                    print("[INFO] Process hanging(?), starting new thread ...")
                    processing = False
            task = queue.pop(0)
            threading.Thread(target=run_task, args=(task,)).start()
        time.sleep(5)

# Start the queue checker in a new thread
threading.Thread(target=check_queue, daemon=True).start()

# Test if the webserver is running
@app.route('/healthcheck')
def healthcheck():
    global processing
    # Check how many threads are running
    threads = threading.enumerate()
    return jsonify(status="OK", processing=processing, threads=len(threads))

# Check the current queue
@app.route('/queue')
def get_queue():
    return jsonify(queue)

@app.route('/upload', methods=['POST'])
def upload():
    input_video = request.files['input_video']
    input_audio = request.files['input_audio']
    # Check if input video is not an mp4 or input_audio is not a wav, and if so, return an error
    if input_video.filename.split('.')[-1] != 'mp4' or input_audio.filename.split('.')[-1] != 'wav':
        return jsonify(success=False, message='[ERROR] Invalid file type, make sure input_video is an mp4 and input_audio is a wav')
    # Generate a random task ID, which must be unique
    while True:
        task_id = str(random.randint(1000, 9999))
        if not os.path.exists(os.path.join(maindirectory, '..', 'tasks', task_id)):
            break
    # Create the directory and status.txt file
    os.makedirs(os.path.join(maindirectory, '..', 'tasks', task_id))
    with open(os.path.join(maindirectory, '..', 'tasks', task_id, 'status.txt'), 'w') as status_file:
        status_file.write('Pending')
    # Add the task to the queue
    queue.append({'input_video': input_video.filename, 'input_audio': input_audio.filename, 'task_id': task_id})
    # Save the input video and audio to the task folder
    input_video.save(os.path.join(maindirectory, '..', 'tasks', task_id, 'input_video.mp4'))
    input_audio.save(os.path.join(maindirectory, '..', 'tasks', task_id, 'input_audio.wav'))
    # Return the task ID
    return jsonify(success=True, task_id=task_id)

@app.route('/status')
def get_status():
    task_id = request.args.get('task_id')
    status_file_path = os.path.join(maindirectory, '..', 'tasks', task_id, 'status.txt')
    if os.path.exists(status_file_path):
        with open(status_file_path, 'r') as status_file:
            status = status_file.read()
        return jsonify(success=True, message=status)
    else:
        return jsonify(success=False, message='[ERROR] Task not found')

@app.route('/download')
def download():
    task_id = request.args.get('task_id')
    result_file_path = os.path.join(maindirectory, '..', 'tasks', task_id, 'result.mp4')
    if os.path.exists(result_file_path):
        return send_file(result_file_path, as_attachment=True)
    else:
        return jsonify(success=False, message='[ERROR] Task not found')

@app.route('/cleanup')
def cleanup():
    # Remove all folders inside tasks folder
    tasks_folder = os.path.join(maindirectory, '..', 'tasks')
    for folder in os.listdir(tasks_folder):
        folder_path = os.path.join(tasks_folder, folder)
        if os.path.isdir(folder_path):
            for file in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file)
                os.remove(file_path)
            os.rmdir(folder_path)
    return jsonify(success=True, message='[INFO] All tasks have been removed')

if __name__ == '__main__':
    # Try to get port from environment variable if set
    if 'PORT' in os.environ:
        port = os.environ['PORT']
    else:
        port = 5000
    # Check if the model exists in the checkpoints folder
    GAN_PATH = os.path.join(maindirectory, '..', 'checkpoints', 'wav2lip_gan.pth')
    WAV2LIP_PATH = os.path.join(maindirectory, '..', 'checkpoints', 'wav2lip.pth')
    FACEDETECT_PATH = os.path.join(maindirectory, '..', 'face_detection', 'detection', 'sfd', 's3fd.pth')
    # If any are missing, download from the given environment variables with _SITE
    if not os.path.exists(GAN_PATH) or not os.path.exists(WAV2LIP_PATH) or not os.path.exists(FACEDETECT_PATH):
        print("[INFO] Missing model(s), downloading from given environment variables ...")
        if 'GAN_SITE' in os.environ:
            GAN_SITE = os.environ['GAN_SITE']
            subprocess.run(["wget", GAN_SITE, "-O", GAN_PATH])
        if 'WAV2LIP_SITE' in os.environ:
            WAV2LIP_SITE = os.environ['WAV2LIP_SITE']
            subprocess.run(["wget", WAV2LIP_SITE, "-O", WAV2LIP_PATH])
        if 'FACEDETECT_SITE' in os.environ:
            FACEDETECT_SITE = os.environ['FACEDETECT_SITE']
            subprocess.run(["wget", FACEDETECT_SITE, "-O", FACEDETECT_PATH])
    # If still missing, raise error
    if not os.path.exists(GAN_PATH) or not os.path.exists(WAV2LIP_PATH) or not os.path.exists(FACEDETECT_PATH):
        print("[ERROR] Missing model(s), or environment vars not set in `.env`. Please check the `.env.example` file for examples. Exiting ...")
        exit(1)
    # Start the webserver
    print(f"[INFO] Starting webserver on port {port} ...")
    serve(app, host='0.0.0.0', port=port)
