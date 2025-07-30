# YouTube Subtitle Generator

A Python tool that generates subtitles from YouTube videos using OpenAI's Whisper model. Now with support for Google Colab and batch processing of multiple videos/podcasts!

## Features

- **Single video processing**: Generate subtitles for individual YouTube videos
- **Batch processing**: Process multiple videos/podcast episodes at once
- **Multiple output formats**: Save results as TXT, CSV, or JSON files
- **Google Colab support**: Run in browser with Jupyter notebook interface
- **High-quality transcription**: Uses OpenAI's Whisper model
- **Flexible model selection**: Choose from tiny to large Whisper models
- **Automatic file management**: Safe filename handling and cleanup
- **Command-line interface**: Full CLI support with various options

## Requirements

- Python 3.7+
- FFmpeg
- Required Python packages (see requirements.txt)

## Installation

### Local Installation

1. Clone the repository:
```bash
git clone https://github.com/piotrproszowski/youtube-subtitle-generator.git
cd youtube-subtitle-generator
```

2. Install FFmpeg:

- **Windows**: 
  - Download FFmpeg from: https://ffmpeg.org/download.html
  - Add FFmpeg path to PATH environment variables

- **macOS**: 
  ```bash
  brew install ffmpeg
  ```

- **Linux (Ubuntu/Debian)**:
  ```bash
  sudo apt-get install ffmpeg
  ```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

### Google Colab

For Google Colab usage, open the `youtube_subtitle_generator_colab.ipynb` notebook in Google Colab. The notebook includes:
- Automatic dependency installation
- Interactive widgets for easy use
- File download capabilities
- Batch processing interface

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/piotrproszowski/youtube-subtitle-generator/blob/main/youtube_subtitle_generator_colab.ipynb)

## Usage

### Command Line Interface

#### Single Video Processing

```bash
# Interactive mode (default)
python subsCollector.py

# Direct URL processing
python subsCollector.py --url https://www.youtube.com/watch?v=VIDEO_ID
```

#### Batch Processing

```bash
# Process multiple URLs from command line
python subsCollector.py --batch-urls url1 url2 url3 --output-format csv

# Process URLs from file
python subsCollector.py --batch-file urls.txt --output-format json

# Process with different Whisper model
python subsCollector.py --batch-file urls.txt --model large --output-format all
```

#### Command Line Options

- `--url URL`: Process a single YouTube video
- `--batch-file FILE`: Process URLs from a text file (one URL per line)
- `--batch-urls URL1 URL2 ...`: Process multiple URLs directly
- `--model {tiny,base,small,medium,large}`: Choose Whisper model (default: base)
- `--output-dir DIR`: Specify output directory (default: downloads)
- `--output-format {txt,csv,json,all}`: Choose output format for batch processing

#### Examples

```bash
# Single video with large model
python subsCollector.py --url https://www.youtube.com/watch?v=dQw4w9WgXcQ --model large

# Batch processing with CSV output
python subsCollector.py --batch-file podcast_episodes.txt --output-format csv

# Multiple URLs with all output formats
python subsCollector.py --batch-urls \
  https://www.youtube.com/watch?v=VIDEO1 \
  https://www.youtube.com/watch?v=VIDEO2 \
  --output-format all

# Custom output directory
python subsCollector.py --batch-file urls.txt --output-dir ./transcripts --output-format json
```

### Batch File Format

Create a text file with YouTube URLs (one per line):

```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
https://youtu.be/another_video_id
https://www.youtube.com/watch?v=third_video
```

Lines starting with `#` are treated as comments and ignored.

### Output Formats

#### TXT Files (Default)
Individual text files for each video containing the transcript.

#### CSV Format
A single CSV file with columns:
- `title`: Video title
- `url`: Original YouTube URL
- `duration`: Video duration
- `transcript`: Full transcript text
- `filename`: Generated filename
- `processed_at`: Processing timestamp

#### JSON Format
A single JSON file containing an array of objects with detailed information for each processed video.

### Google Colab Usage

1. Open the `youtube_subtitle_generator_colab.ipynb` notebook in Google Colab
2. Run the setup cells to install dependencies
3. Use the interactive widgets to:
   - Process single videos
   - Batch process multiple videos
   - Download results in various formats
   - Manage generated files

The Colab notebook provides:
- Interactive interface with widgets
- Progress tracking for batch processing
- Automatic file downloads
- ZIP file creation for easy download
- Real-time processing updates

## Whisper Model Comparison

| Model  | Size | Speed | Accuracy | Use Case |
|--------|------|-------|----------|----------|
| tiny   | 39 MB | Fastest | Good | Quick processing, testing |
| base   | 74 MB | Fast | Better | Default, balanced performance |
| small  | 244 MB | Medium | Good | Better accuracy |
| medium | 769 MB | Slow | Very Good | High accuracy needs |
| large  | 1550 MB | Slowest | Best | Maximum accuracy |

## Best Practices

### For Podcasts and Long Content
- Use `medium` or `large` models for better accuracy
- Process in batches to avoid timeouts
- Use CSV or JSON output for easy analysis
- Consider using `--output-dir` to organize different podcast series

### For Quick Testing
- Use `tiny` or `base` models for faster processing
- Start with small batches to test your URLs

### For Production Use
- Use `large` model for best quality
- Always backup your URL lists
- Monitor disk space for large batch jobs

## File Structure

After processing, your directory will contain:
```
downloads/
├── video_title_1.txt
├── video_title_2.txt
├── subtitles_results.csv    # If CSV format selected
├── subtitles_results.json   # If JSON format selected
└── ...
```

## Troubleshooting

### Common Issues

1. **FFmpeg not found**: Install FFmpeg and ensure it's in your PATH
2. **Invalid URL**: Ensure URLs are valid YouTube links (youtube.com or youtu.be)
3. **Memory errors**: Use smaller Whisper models or process fewer videos at once
4. **Permission errors**: Check write permissions in output directory

### Error Messages

- `Wrong whisper library installed`: Run `pip uninstall whisper && pip install openai-whisper`
- `FFmpeg is not installed`: Install FFmpeg for your operating system
- `Audio file not found`: Video download failed, check URL validity

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License
