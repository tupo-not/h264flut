# h264flut

pixelflut but with h264 and GStreamer<br><br>
Default resolution is 800x600<br>
Default codec is h264<br>
Default channels count is 9<br>
Currently no audio support<br>
pls use multichannel version, its fun:D
<br>

## How it works<br>

Client runs `ffmpeg -re -f lavfi -i testsrc -vf "scale=800:600" -c:v libx264 -f rtp udp://A.B.C.D:5000 + (preffered number of channel)` (for example)<br>
RTP H264 Traffic goes to `A.B.C.D:5003 (channel 3)`<br>
GStreamer channel pipeline receives it, triggering fallback switch and shows it on channel's output<br>
If in 1 second(default) channel pipeline dont receive at least one frame, fallbackswitch shows `NOVIDEO0)0))`<br><br>
<br>

## Dependencies

gst-plugins-good<br>
gst-plugins-base<br>
gst-plugin-fallbackswitch<br>
gst-libav<br>
gst-python
