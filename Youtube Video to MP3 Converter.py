import json
import os
import re
import urllib.request

from pytubefix import YouTube

# moviepy 2.x removed the moviepy.editor module; fall back accordingly.
try:
    from moviepy.editor import AudioFileClip  # moviepy < 2
except ImportError:  # pragma: no cover - only hit on moviepy >= 2
    from moviepy import AudioFileClip  # type: ignore[import-untyped]  # moviepy >= 2

MUSIC_ROOT = r'G:\Unreleased Snippets'
LMSTUDIO_URL = 'http://localhost:1234/v1/chat/completions'
LMSTUDIO_MODEL = 'google/gemma-4-e4b'

# Prompt directions for the judge model. It must (a) scrub non-name parts out of
# the title, (b) subtract the artist name once discovered, and (c) fuzzy-match
# the artist against the existing library folders.
JUDGE_PROMPT = """You are a music-metadata parser. Given a YouTube video title and the list of artist folder names in my music library, decide where this song belongs.

Rules:
1. The SONG NAME is the actual title of the track only. Strip out everything that is not part of the song name: parenthetical tags such as (Official Audio), (Official Video), (Visualizer), (Lyric Video), (Remastered 2011), quality/format words, and any "feat."/"ft." collaborator credits are NOT part of the song name.
2. The ARTIST is the primary performer of the track (not featured artists). If a folder in my library matches the artist, use that folder. Matching must be fuzzy: nicknames, abbreviations, misspellings and extra words count as matches - e.g. "Uzi" = Lil Uzi Vert, "Juice Wrld" = Juice WRLD, "Carti" = Playboi Carti.
3. Do NOT include the artist name inside the song name (subtract it once discovered).
4. If no folder plausibly matches the artist, set matched_folder to null.

Video title: {title}
Library folders: {folders}

Respond with ONLY a JSON object, no other text: {{"artist": "...", "song_name": "...", "matched_folder": "..." or null}}"""


def ask_judge(title, folders):
    """Ask the local Gemma model (hosted by LM Studio) to parse the title."""
    prompt = JUDGE_PROMPT.format(title=title, folders=", ".join(folders))
    body = json.dumps({
        'model': LMSTUDIO_MODEL,
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 0,
    }).encode()
    req = urllib.request.Request(
        LMSTUDIO_URL, data=body, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = json.load(resp)
    return data['choices'][0]['message']['content']


def parse_judge_reply(reply):
    """Extract the JSON object from the model reply (tolerates code fences)."""
    text = re.sub(r'```(?:json)?', '', reply).strip().strip('`').strip()
    start, end = text.find('{'), text.rfind('}')
    if start == -1 or end == -1:
        raise ValueError(f"No JSON object in model reply: {reply!r}")
    return json.loads(text[start:end + 1])


def sanitize(name):
    """Make a string safe to use as a file/folder name."""
    return re.sub(r'[\\/:*?"<>|]', ' ', name).strip() or 'Unknown'


link = input("Enter URL:")

# NOTE: do NOT pass use_oauth=True here. pytubefix's OAuth device flow is
# broken (Google now answers the device-code endpoint with HTTP 428), which
# crashes the script before any download happens. Plain YouTube(url=...) works.
yt = YouTube(url=link)

# We only need audio for an MP3, so grab the best audio-only stream instead of
# a video stream (this video has no progressive video+audio streams at all).
audio = yt.streams.get_audio_only()
if audio is None:
    raise SystemExit("No audio-only stream available for this video.")

# --- Ask the judge model where this song belongs -----------------------------
folders = [d for d in os.listdir(MUSIC_ROOT) if os.path.isdir(os.path.join(MUSIC_ROOT, d))]
print("Asking judge model to parse title...")
try:
    verdict = parse_judge_reply(ask_judge(yt.title, folders))
except Exception as e:
    print(f"Judge model unavailable/failed ({e}); falling back to 'Misc' folder.")
    verdict = {'artist': yt.title, 'song_name': sanitize(yt.title), 'matched_folder': None}

# Fuzzy-match the model's chosen folder against what actually exists on disk.
def find_existing_folder(name):
    if not name:
        return None
    low = str(name).strip().lower()
    for d in folders:
        if d.lower() == low:
            return d
    return None

matched = find_existing_folder(verdict.get('matched_folder'))
if matched:
    destination = os.path.join(MUSIC_ROOT, matched)
else:  # no existing folder matches -> create one named after the artist
    destination = os.path.join(MUSIC_ROOT, sanitize(verdict.get('artist', 'Misc')))
os.makedirs(destination, exist_ok=True)  # download() fails if this dir is missing

print(f"Judge says: artist={verdict.get('artist')!r} song={verdict.get('song_name')!r} -> {destination}")

outFile = audio.download(output_path=destination)
if not outFile:
    raise SystemExit("Download failed - no file returned.")

base, ext = os.path.splitext(outFile)
newFile = base + (".m4a")  # audio-only streams arrive as .m4a (MP4 container), not video
if newFile != outFile:
    os.rename(outFile, newFile)

print (yt.title + " has been successfully downloaded!")


def convert_m4a_to_mp3(m4a_path, mp3_path):
    """
    Converts an M4A audio file to an MP3 audio file.

    Args:
        m4a_path (str): The path to the input M4A file.
        mp3_path (str): The path for the output MP3 file.
    """
    try:
        # AudioFileClip reads the audio directly - no video decoding needed,
        # and it works with both moviepy 1.x and 2.x.
        audio_clip = AudioFileClip(m4a_path)
        audio_clip.write_audiofile(mp3_path)
        audio_clip.close()
        print(f"Successfully converted '{m4a_path}' to '{mp3_path}'")
        os.remove(m4a_path)
    except Exception as e:
        print(f"Error converting file: {e}")

# Name the final MP3 as "[artist name] - [song name]" (the judge already
# subtracted the artist from song_name, so no duplication).
artist_name = sanitize(verdict.get('artist', 'Unknown'))
song_name = sanitize(verdict.get('song_name', 'Unknown'))
input_m4a_file = newFile  # The downloaded audio file
output_mp3_file = os.path.join(destination, f"{artist_name} - {song_name}.mp3")

convert_m4a_to_mp3(input_m4a_file, output_mp3_file)

