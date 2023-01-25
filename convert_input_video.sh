#!/bin/bash

input_video="input_video.mp4"

# Remove existing temp directory
rm -rf temp

# Create new temp directory
mkdir temp

# Split video into segments and save in temp directory
ffmpeg -i $input_video -c copy -an -map 0 -segment_time 00:00:15 -f segment -reset_timestamps 1 temp/input_video%d.mp4

# Split audio from video and convert to wav, save in temp directory
ffmpeg -i $input_video -c copy -map 0:a -f segment -segment_time 00:00:15 -reset_timestamps 1 -acodec pcm_s16le -ar 44100 -ac 2 temp/input_audio%d.wav

# Count number of segments
n_segments=$(ls temp | grep "input_video" | wc -l)

# Move video and audio segments to corresponding directories
for i in $(seq 0 $((n_segments-1))); do
    mkdir $i
    mv temp/input_video$i.mp4 $i/input_video.mp4
    mv temp/input_audio$i.wav $i/input_audio.wav
done

# Save number of segments to length.txt
echo $n_segments > length.txt
