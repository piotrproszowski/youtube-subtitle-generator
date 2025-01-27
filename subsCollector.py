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
    """Check if FFmpeg is installed."""
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
            safe_name = "".join(x for x in video_title if x.isalnum() or x in (' ', '-', '_'))
            safe_name = safe_name.replace(' ', '_')
            return safe_name[:100]

    def extract_subtitles(self, video_url: str) -> Optional[str]:
        """
        Downloads audio from video and generates transcription.
        Args:
            video_url: YouTube video URL
        Returns:
            str: Generated subtitles or None if error occurs
        """
        try:
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)

            safe_filename = self._get_safe_filename(video_url)
            audio_path = os.path.join(self.output_dir, safe_filename)
            text_path = os.path.join(self.output_dir, safe_filename + '.txt')
            
            audio_path = os.path.abspath(audio_path)

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

            print("Downloading audio...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])

            print("Generating subtitles...")
            final_audio_path = audio_path + '.mp3'
            if not os.path.exists(final_audio_path):
                raise FileNotFoundError(f"Audio file not found at: {final_audio_path}")
            
            result = self.model.transcribe(final_audio_path)
            
            if os.path.exists(final_audio_path):
                os.remove(final_audio_path)
            
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(result["text"])
            
            return result["text"]

        except Exception as e:
            print(f"Error during processing: {str(e)}")
            if 'final_audio_path' in locals() and os.path.exists(final_audio_path):
                os.remove(final_audio_path)
            return None

def main():
    check_ffmpeg()
    
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
        print("\nGenerated subtitles have been saved to file in 'downloads' directory")
        print("\nFirst 500 characters of subtitles:")
        print(subtitles[:500] + "...")
    else:
        print("Failed to generate subtitles.")

if __name__ == "__main__":
    main()