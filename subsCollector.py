import os
import yt_dlp
import shutil
try:
    import whisper
except AttributeError:
    print("Error: Wrong whisper library installed.")
    print("Please run the following commands:")
    print("pip uninstall whisper")
    print("pip install openai-whisper")
    exit(1)
from typing import Optional

def check_ffmpeg():
    """Sprawdza czy FFmpeg jest zainstalowany w systemie."""
    if not shutil.which('ffmpeg'):
        print("Error: FFmpeg is not installed!")
        print("\nTo install FFmpeg:")
        print("\nOn macOS (using Homebrew):")
        print("brew install ffmpeg")
        print("\nOn Ubuntu/Debian:")
        print("sudo apt-get install ffmpeg")
        print("\nOn Windows:")
        print("1. Download FFmpeg from: https://ffmpeg.org/download.html")
        print("2. Add FFmpeg path to PATH environment variables")
        exit(1)

class SubtitleExtractor:
    def __init__(self, model_name: str = "base"):
        """
        Initialize subtitle extractor.
        Args:
            model_name: Whisper model name ('tiny', 'base', 'small', 'medium', 'large')
        """
        self.model = whisper.load_model(model_name)
        self.output_dir = "downloads"
        os.makedirs(self.output_dir, exist_ok=True)

    def _get_safe_filename(self, video_url: str) -> str:
        """Gets safe filename based on video title."""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            video_title = info['title']
            return "".join(x for x in video_title if x.isalnum() or x in (' ', '-', '_'))[:100]

    def extract_subtitles(self, video_url: str) -> Optional[str]:
        """
        Downloads audio from video and generates transcription.
        Args:
            video_url: YouTube video URL
        Returns:
            str: Generated subtitles or None if error occurs
        """
        try:
            safe_filename = self._get_safe_filename(video_url)
            audio_path = os.path.join(self.output_dir, f"{safe_filename}.mp3")

            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': audio_path,
                'quiet': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])

            result = self.model.transcribe(audio_path)
            os.remove(audio_path)
            
            return result["text"]

        except Exception as e:
            print(f"Error during processing: {str(e)}")
            return None

def main():
    # Sprawdzenie FFmpeg przed rozpoczęciem
    check_ffmpeg()
    
    # Pobieranie linku od użytkownika
    print("Enter YouTube video URL:")
    video_url = input().strip()
    
    if not video_url:
        print("No URL provided!")
        return
        
    if "youtube.com" not in video_url and "youtu.be" not in video_url:
        print("The provided URL is not a YouTube link!")
        return
    
    extractor = SubtitleExtractor(model_name="base")
    print("Starting video processing...")
    subtitles = extractor.extract_subtitles(video_url)
    
    if subtitles:
        print("\nGenerated subtitles:")
        print(subtitles)
    else:
        print("Failed to generate subtitles.")

if __name__ == "__main__":
    main()