# mkv2mp4

## Introduction
`mkv2mp4` is a simple, yet effective Python script for converting MKV video files to MP4 format. This script scans the directory it's placed in for any `.mkv` files and efficiently converts them to `.mp4` format, saving them in the same directory. It's designed to be lightweight, fast, and easy to use.

## Features
- **Batch Conversion**: Converts all MKV files in the script's directory.
- **Fast Processing**: Utilizes FFmpeg's stream copying feature for quick conversion without re-encoding (when possible).
- **Ease of Use**: Just place the script in the desired directory and run it.

## Prerequisites
Before you begin, ensure you have met the following requirements:
- **Python**: The script is written in Python. Make sure you have Python installed on your system.
- **FFmpeg**: `mkv2mp4` uses FFmpeg for video conversion. Install FFmpeg from [FFmpeg's official website](https://ffmpeg.org/download.html).

## Installation
1. Clone the repository or download the script directly into the directory where your MKV files are located.
2. Install FFmpeg if you haven't already (see prerequisites).

## Usage
To use `mkv2mp4`, follow these steps:
1. Place the `mkv2mp4.py` script in the directory with your MKV files.
2. Run the script: python mkv2mp4.py
3. The script will automatically find and convert all MKV files to MP4 format in the same directory.

## Contributing
Contributions to `mkv2mp4` are welcome. Feel free to fork the repository and submit pull requests.

## License
This project is licensed under the [MIT License](LICENSE).

## Contact
If you have any questions or suggestions, please open an issue in the GitHub repository.
