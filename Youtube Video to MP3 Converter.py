from pytubefix import YouTube
from moviepy.editor import VideoFileClip
import os
link = input("Enter URL:")
yt = YouTube(url=link,use_oauth=True,allow_oauth_cache=True)

video = yt.streams.filter(only_audio=False, only_video= False).first()

#print("Enter destination (leave blank for current destination): ")
destination = str('E:\\Unreleased Snippets\\Pierre')
outFile = video.download(output_path=destination)

base, ext = os.path.splitext(outFile)
newFile = base + (".mp4")
os.rename(outFile, newFile)

print (yt.title + " has been successfully downloaded!")
yt.client = 'web'



def convert_mp4_to_mp3(mp4_path, mp3_path):
    """
    Converts an MP4 video file to an MP3 audio file.
    
    Args:
        mp4_path (str): The path to the input MP4 file.
        mp3_path (str): The path for the output MP3 file.
    """
    try:
        video_clip = VideoFileClip(mp4_path)
        audio_clip = video_clip.audio
        audio_clip.write_audiofile(mp3_path)
        audio_clip.close()
        video_clip.close()
        print(f"Successfully converted '{mp4_path}' to '{mp3_path}'")
        os.remove(mp4_path)
    except Exception as e:
        print(f"Error converting file: {e}")

    # Example usage:
input_mp4_file = newFile  # Replace with your MP4 file path
output_mp3_file = base + ".mp3" # Replace with your desired output MP3 file path

convert_mp4_to_mp3(input_mp4_file, output_mp3_file)

