import os
from yt_dlp import YoutubeDL

# moviepy 2.x removed the moviepy.editor module; fall back accordingly.
try:
    from moviepy.editor import AudioFileClip  # moviepy < 2
except ImportError:
    from moviepy import AudioFileClip  # moviepy >= 2


def download_and_convert(youtube_url):
    # 1. Setup download options for yt-dlp.
    # Only the audio stream is needed, so no video+audio merge (which would
    # require a system ffmpeg on PATH) and no pointless video data is fetched.
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(os.getcwd(), 'downloaded_audio.%(ext)s'),
    }

    print("Starting download...")
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=True)
        audio_filename = ydl.prepare_filename(info)

    mp3_filename = os.path.splitext(audio_filename)[0] + ".mp3"

    # 2. Convert the downloaded audio to MP3 using MoviePy (it bundles its own ffmpeg)
    if os.path.exists(audio_filename):
        print("Converting to MP3...")
        clip = AudioFileClip(audio_filename)
        clip.write_audiofile(mp3_filename, codec='mp3')
        clip.close()
        os.remove(audio_filename)
        print(f"Success! Audio saved as {mp3_filename}")
    else:
        print("Download failed.")

if __name__ == "__main__":
    url = input("Enter YouTube URL: ")
    download_and_convert(url)
