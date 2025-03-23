import os
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any

import yt_dlp
import shutil
try:
    import whisper
except AttributeError:
    logging.error("Error: Wrong whisper library installed.")
    logging.error("Please run the following commands:")
    logging.error("pip uninstall whisper")
    logging.error("pip install openai-whisper")
    exit(1)

# Configuration
class WhisperModel(Enum):
    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"

@dataclass
class AppConfig:
    """Application configuration settings."""
    output_directory: Path = Path("downloads")
    default_model: WhisperModel = WhisperModel.BASE
    audio_format: str = "mp3"
    audio_quality: str = "192"
    max_filename_length: int = 100

class FFmpegValidator:
    """Validates FFmpeg installation and provides installation instructions."""
    
    @staticmethod
    def check_installation() -> None:
        """
        Verifies if FFmpeg is installed and accessible.
        Raises:
            SystemExit: If FFmpeg is not installed.
        """
        if not shutil.which('ffmpeg'):
            installation_instructions = {
                "darwin": "brew install ffmpeg",
                "linux": "sudo apt-get install ffmpeg",
                "win32": "1. Download FFmpeg from: https://ffmpeg.org/download.html\n"
                        "2. Add FFmpeg path to PATH environment variables"
            }
            
            logging.error("FFmpeg is not installed!")
            platform = os.sys.platform
            instruction = installation_instructions.get(
                platform, 
                "Please install FFmpeg for your operating system"
            )
            logging.error(f"Installation instructions:\n{instruction}")
            raise SystemExit(1)

class YouTubeAudioExtractor:
    """Handles downloading audio from YouTube videos."""
    
    def __init__(self, config: AppConfig):
        self.config = config
        
    def get_video_info(self, video_url: str) -> Dict[str, Any]:
        """
        Retrieves video information without downloading.
        
        Args:
            video_url: YouTube video URL
            
        Returns:
            Dict containing video information
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(video_url, download=False)
    
    def create_safe_filename(self, video_title: str) -> str:
        """
        Creates a safe filename from video title.
        
        Args:
            video_title: Original video title
            
        Returns:
            Sanitized filename
        """
        safe_chars = (char for char in video_title if char.isalnum() or char in (' ', '-', '_'))
        safe_name = "".join(safe_chars).replace(' ', '_')
        return safe_name[:self.config.max_filename_length]
    
    def download_audio(self, video_url: str, output_path: Path) -> Path:
        """
        Downloads audio from YouTube video.
        
        Args:
            video_url: YouTube video URL
            output_path: Path to save the audio file
            
        Returns:
            Path to downloaded audio file
        """
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': self.config.audio_format,
                'preferredquality': self.config.audio_quality,
            }],
            'outtmpl': str(output_path),
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        return output_path.with_suffix(f".{self.config.audio_format}")

class SubtitleGenerator:
    """Generates subtitles from audio using Whisper model."""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.model = whisper.load_model(config.default_model.value)
        self.youtube_extractor = YouTubeAudioExtractor(config)
        self.config.output_directory.mkdir(exist_ok=True)
        
    def generate_subtitles(self, video_url: str) -> Optional[str]:
        """
        Generates subtitles for a YouTube video.
        
        Args:
            video_url: YouTube video URL
            
        Returns:
            Generated subtitles text or None if failed
        """
        try:
            video_info = self.youtube_extractor.get_video_info(video_url)
            safe_filename = self.youtube_extractor.create_safe_filename(video_info['title'])
            
            audio_path = self.config.output_directory / safe_filename
            text_path = audio_path.with_suffix('.txt')
            
            logging.info("Downloading audio...")
            final_audio_path = self.youtube_extractor.download_audio(video_url, audio_path)
            
            if not final_audio_path.exists():
                raise FileNotFoundError(f"Audio file not found at: {final_audio_path}")
            
            logging.info("Generating subtitles...")
            result = self.model.transcribe(str(final_audio_path))
            
            final_audio_path.unlink()  # Clean up audio file
            
            text_path.write_text(result["text"], encoding='utf-8')
            logging.info(f"Subtitles saved to: {text_path}")
            
            return result["text"]
            
        except Exception as e:
            logging.error(f"Failed to generate subtitles: {str(e)}")
            if 'final_audio_path' in locals() and final_audio_path.exists():
                final_audio_path.unlink()
            return None

def setup_logging():
    """Configures application logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def validate_youtube_url(url: str) -> bool:
    """
    Validates if the provided URL is a YouTube link.
    
    Args:
        url: URL to validate
        
    Returns:
        bool: True if URL is valid YouTube link
    """
    return any(domain in url for domain in ["youtube.com", "youtu.be"])

def main():
    """Main application entry point."""
    setup_logging()
    
    try:
        FFmpegValidator.check_installation()
        
        video_url = input("Enter YouTube video URL: ").strip()
        
        if not video_url:
            logging.error("No URL provided!")
            return
            
        if not validate_youtube_url(video_url):
            logging.error("The provided URL is not a YouTube link!")
            return
        
        config = AppConfig()
        generator = SubtitleGenerator(config)
        
        logging.info("Starting video processing...")
        subtitles = generator.generate_subtitles(video_url)
        
        if subtitles:
            logging.info("Generated subtitles have been saved to file in 'downloads' directory")
            logging.info("\nFirst 500 characters of subtitles:")
            print(f"{subtitles[:500]}...")
        else:
            logging.error("Failed to generate subtitles.")
            
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main()