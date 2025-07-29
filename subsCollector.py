import os
import logging
import argparse
import json
import csv
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

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

    def generate_single_subtitle_detailed(self, video_url: str) -> Optional[Dict[str, Any]]:
        """
        Generates subtitles for a single YouTube video with detailed information.
        
        Args:
            video_url: YouTube video URL
            
        Returns:
            Dict with detailed information or None if failed
        """
        try:
            if not validate_youtube_url(video_url):
                logging.error(f"Invalid YouTube URL: {video_url}")
                return None
                
            video_info = self.youtube_extractor.get_video_info(video_url)
            safe_filename = self.youtube_extractor.create_safe_filename(video_info['title'])
            
            audio_path = self.config.output_directory / safe_filename
            text_path = audio_path.with_suffix('.txt')
            
            logging.info(f"Processing: {video_info['title']}")
            final_audio_path = self.youtube_extractor.download_audio(video_url, audio_path)
            
            if not final_audio_path.exists():
                raise FileNotFoundError(f"Audio file not found at: {final_audio_path}")
            
            result = self.model.transcribe(str(final_audio_path))
            
            # Clean up audio file
            final_audio_path.unlink()
            
            # Save text file
            text_path.write_text(result["text"], encoding='utf-8')
            
            return {
                'url': video_url,
                'title': video_info['title'],
                'transcript': result["text"],
                'filename': safe_filename,
                'text_file': str(text_path),
                'duration': video_info.get('duration', 'Unknown'),
                'processed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Failed to generate subtitles for {video_url}: {str(e)}")
            if 'final_audio_path' in locals() and final_audio_path.exists():
                final_audio_path.unlink()
            return None

    def generate_batch_subtitles(self, video_urls: List[str]) -> List[Dict[str, Any]]:
        """
        Generates subtitles for multiple YouTube videos.
        
        Args:
            video_urls: List of YouTube video URLs
            
        Returns:
            List of dictionaries with detailed information for each processed video
        """
        results = []
        
        for i, url in enumerate(video_urls, 1):
            logging.info(f"Processing video {i}/{len(video_urls)}: {url}")
            result = self.generate_single_subtitle_detailed(url.strip())
            if result:
                results.append(result)
                logging.info(f"✓ Completed: {result['title']}")
            else:
                logging.error(f"✗ Failed to process: {url}")
                
        return results
    
    def save_results_csv(self, results: List[Dict[str, Any]], filename: str = "subtitles_results.csv") -> Path:
        """Saves results to CSV file."""
        csv_path = self.config.output_directory / filename
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            if results:
                fieldnames = ['title', 'url', 'duration', 'transcript', 'filename', 'processed_at']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for result in results:
                    writer.writerow({
                        'title': result['title'],
                        'url': result['url'],
                        'duration': result['duration'],
                        'transcript': result['transcript'],
                        'filename': result['filename'],
                        'processed_at': result['processed_at']
                    })
        
        logging.info(f"CSV results saved to: {csv_path}")
        return csv_path
    
    def save_results_json(self, results: List[Dict[str, Any]], filename: str = "subtitles_results.json") -> Path:
        """Saves results to JSON file."""
        json_path = self.config.output_directory / filename
        
        with open(json_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(results, jsonfile, indent=2, ensure_ascii=False)
        
        logging.info(f"JSON results saved to: {json_path}")
        return json_path

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

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Generate subtitles from YouTube videos using OpenAI Whisper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Single video:
    python subsCollector.py --url https://www.youtube.com/watch?v=VIDEO_ID
    
  Batch processing:
    python subsCollector.py --batch-file urls.txt --output-format csv
    python subsCollector.py --batch-urls url1 url2 url3 --output-format json
    
  Interactive mode (default):
    python subsCollector.py
        """
    )
    
    # Mode selection
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--url', type=str, help='Single YouTube video URL to process')
    mode_group.add_argument('--batch-file', type=str, help='File containing YouTube URLs (one per line)')
    mode_group.add_argument('--batch-urls', nargs='+', help='Multiple YouTube URLs separated by spaces')
    
    # Configuration options
    parser.add_argument('--model', type=str, choices=['tiny', 'base', 'small', 'medium', 'large'],
                        default='base', help='Whisper model to use (default: base)')
    parser.add_argument('--output-dir', type=str, default='downloads',
                        help='Output directory for generated files (default: downloads)')
    parser.add_argument('--output-format', choices=['txt', 'csv', 'json', 'all'],
                        default='txt', help='Output format for batch processing (default: txt)')
    
    return parser.parse_args()

def process_batch_from_file(file_path: str) -> List[str]:
    """Load URLs from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f.readlines() if line.strip()]
        return urls
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        return []
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {str(e)}")
        return []

def main():
    """Main application entry point."""
    setup_logging()
    
    try:
        FFmpegValidator.check_installation()
        
        args = parse_arguments()
        
        # Create configuration
        config = AppConfig(
            output_directory=Path(args.output_dir),
            default_model=WhisperModel(args.model)
        )
        
        generator = SubtitleGenerator(config)
        
        # Single URL mode
        if args.url:
            logging.info("Processing single video...")
            if not validate_youtube_url(args.url):
                logging.error("The provided URL is not a YouTube link!")
                return
                
            subtitles = generator.generate_subtitles(args.url)
            if subtitles:
                logging.info("Generated subtitles have been saved to file in downloads directory")
                logging.info("\nFirst 500 characters of subtitles:")
                print(f"{subtitles[:500]}...")
            else:
                logging.error("Failed to generate subtitles.")
        
        # Batch processing from file
        elif args.batch_file:
            logging.info(f"Loading URLs from file: {args.batch_file}")
            video_urls = process_batch_from_file(args.batch_file)
            if not video_urls:
                logging.error("No valid URLs found in file")
                return
                
            logging.info(f"Processing {len(video_urls)} videos in batch mode...")
            results = generator.generate_batch_subtitles(video_urls)
            
            if results:
                logging.info(f"Successfully processed {len(results)}/{len(video_urls)} videos")
                
                # Save in requested formats
                if args.output_format in ['csv', 'all']:
                    csv_path = generator.save_results_csv(results)
                    
                if args.output_format in ['json', 'all']:
                    json_path = generator.save_results_json(results)
                    
                logging.info("Batch processing completed!")
            else:
                logging.error("No videos were successfully processed")
        
        # Batch processing from command line URLs
        elif args.batch_urls:
            video_urls = args.batch_urls
            logging.info(f"Processing {len(video_urls)} videos in batch mode...")
            
            # Validate URLs
            valid_urls = [url for url in video_urls if validate_youtube_url(url)]
            if len(valid_urls) != len(video_urls):
                logging.warning(f"Found {len(video_urls) - len(valid_urls)} invalid YouTube URLs")
            
            if not valid_urls:
                logging.error("No valid YouTube URLs provided")
                return
                
            results = generator.generate_batch_subtitles(valid_urls)
            
            if results:
                logging.info(f"Successfully processed {len(results)}/{len(valid_urls)} videos")
                
                # Save in requested formats
                if args.output_format in ['csv', 'all']:
                    csv_path = generator.save_results_csv(results)
                    
                if args.output_format in ['json', 'all']:
                    json_path = generator.save_results_json(results)
                    
                logging.info("Batch processing completed!")
            else:
                logging.error("No videos were successfully processed")
        
        # Interactive mode (default)
        else:
            video_url = input("Enter YouTube video URL: ").strip()
            
            if not video_url:
                logging.error("No URL provided!")
                return
                
            if not validate_youtube_url(video_url):
                logging.error("The provided URL is not a YouTube link!")
                return
            
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