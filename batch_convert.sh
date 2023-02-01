#!/bin/bash

# Read number of segments
n_segments=$(cat "/content/input/length.txt")

# Run inference for each segment
for i in $(seq 0 $((n_segments-1))); do
    python inference.py --checkpoint_path checkpoints/wav2lip_gan.pth --face "/content/input/$i/input_video.mp4" --audio "/content/input/$i/input_audio.wav" --pads 0 20 0 0
    mv /content/Wav2Lip/results/result_voice.mp4 /content/output/segment$i.mp4
done
