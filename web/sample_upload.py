import requests
import os

# Determine main program directory
maindirectory = os.path.dirname(os.path.abspath(__file__)) # The absolute path to this file

def upload_files(video_file_path=None, audio_file_path=None):
    # If file paths are not provided, open file dialogs
    if video_file_path is None:
        import tkinter as tk
        from tkinter import filedialog

        # Create a file dialog for the input video
        root = tk.Tk()
        root.withdraw()
        video_file_path = filedialog.askopenfilename(title="Select input video", filetypes=[("MP4 files", "*.mp4")])

    if audio_file_path is None:
        import tkinter as tk
        from tkinter import filedialog

        # Create a file dialog for the input audio
        root = tk.Tk()
        root.withdraw()
        audio_file_path = filedialog.askopenfilename(title="Select input audio", filetypes=[("WAV files", "*.wav")])

    # Define the URL of the /upload endpoint
    url = "http://localhost:5000/upload"

    # Open the files in binary mode
    video_file = open(video_file_path, 'rb')
    audio_file = open(audio_file_path, 'rb')

    # Send the files to the /upload endpoint
    response = requests.post(url, files={'input_video': video_file, 'input_audio': audio_file})

    # Close the files
    video_file.close()
    audio_file.close()

    # Print the response from the server
    print(response.json())

upload_files(video_file_path=os.path.join(maindirectory, '..', 'tasks', 'test', 'input_video.mp4'), audio_file_path=os.path.join(maindirectory, '..', 'tasks', 'test', 'input_audio.wav'))
