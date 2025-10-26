# h264flut

pixelflut but with h264 and GStreamer<br><br>
Default per channel resolution is 800x600<br>
Default codec is h264<br>
Default audio codec is AAC<br>
Default channels count is 9<br>
<br>
current status: LAGodrom<br>
separated audio track by each channel<br>

## How it works<br>

Client runs `ffmpeg -re -f lavfi -i testsrc -i cocojambo.mp3 -vf "scale=800:600" -c:v libx264 -c:a aac -f mpegts udp://A.B.C.D:5000 + (preffered number of channel)` (for example)<br>
MPEG-TS H264 Traffic goes to `A.B.C.D:5003 (channel 3, counting from 0)`<br>
GStreamer channel pipeline receives it, triggering fallback switch and shows video on its channel's output<br>
If in 1 second(default) channel pipeline dont receive at least one frame, fallbackswitch shows `NOVIDEO0)0))`<br><br>
<br>

## Dependencies

gst-plugins-good<br>
gst-plugins-base<br>
gst-plugin-fallbackswitch<br>
gst-libav<br>
gst-python<br>
archlinux rootfs