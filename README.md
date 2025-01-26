# YouTube Subtitle Generator

A Python tool that generates subtitles from YouTube videos using OpenAI's Whisper model.

## Requirements

- Python 3.7+
- FFmpeg
- Required Python packages (see requirements.txt)

## Installation

1. Clone the repository:

2. Install FFmpeg:

- On Windows:
  - Download FFmpeg from: https://ffmpeg.org/download.html
  - Add FFmpeg path to PATH environment variables

3. Install Python dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the script:

```bash
python subsCollector.py
```

When prompted, enter the YouTube video URL. The script will:

1. Download the audio from the video
2. Generate subtitles using Whisper
3. Display the generated subtitles
4. Clean up temporary files

## Features

- Automatic audio extraction from YouTube videos
- High-quality speech recognition using OpenAI's Whisper model
- Support for various video quality options
- Automatic cleanup of temporary files
- Safe filename handling

## License

MIT License
