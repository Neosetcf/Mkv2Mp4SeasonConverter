import os
import subprocess

# Function to convert MKV to MP4
def convert_mkv_to_mp4(filename):
    output_file = filename.replace('.mkv', '.mp4')
    subprocess.run(['ffmpeg', '-i', filename, '-codec', 'copy', output_file])

# Scan the current directory for MKV files and convert them
for file in os.listdir('.'):
    if file.endswith('.mkv'):
        print(f'Converting {file} to MP4...')
        convert_mkv_to_mp4(file)
        print(f'Converted {file} successfully.')

print('Conversion process completed.')
