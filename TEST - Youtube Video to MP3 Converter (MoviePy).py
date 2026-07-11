import os
from yt_dlp import YoutubeDL
import ffmpeg
from moviepy.editor import VideoFileClip

def download_and_convert(youtube_url):
    # 1. Setup download options for yt-dlp
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'downloaded_video.mp4', # Save temporarily as mp4
    }

    print("Starting download...")
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])
    
    video_filename = "downloaded_video.mp4"
    audio_filename = "final_audio.mp3"

    # 2. Convert MP4 to MP3 using MoviePy
    if os.path.exists(video_filename):
        print("Converting to MP3...")
        video = VideoFileClip(video_filename)
        # Extract audio and save as mp3
        video.audio.write_audiofile(audio_filename, codec='mp3')
        video.close()
        print(f"Success! Audio saved as {audio_filename}")
    else:
        print("Download failed.")

if __name__ == "__main__":
    url = input("Enter YouTube URL: ")
    download_and_convert(url)
