# h264flut

pixelflut but with h264 and GStreamer<br><br>
Default resolution is 800x600<br>
Default codec is h264<br>
Currently no audio support
<br>

## How it works<br>

Client runs `ffmpeg -re -f lavfi -i testsrc -vf "scale=800:600" -c:v libx264 -f rtp udp://A.B.C.D:EEEE` (for example)<br>
RTP H264 Traffic goes to `A.B.C.D:EEEE`<br>
GStreamer pipeline receives it, triggering fallback switch and shows it on autovideosink (replaceable)<br>
If in 5 seconds `(fallback_timeout var in script)` pipeline dont receive at least one frame, fallbackswitch shows screen with "NOVIDEO0)0))" `(novideotext_str str in script)`<br><br>
textoverlay named `bottomtext` and `toptext` overlays on any received video
<br>

## Some options in config.ini
#### Video<br>
 width - Output video width<br>
 height - Output video height<br>
 nogui - Will server use GUI? (y or n)<br>
 fallback_timeout - Fallback switch timeout, in seconds

#### Text<br>
 toptext - Top Text value<br>
 bottomtext - Bottom Text value<br>
 novideotext - novideo Placeholder Text value<br>
 toptext_font - Top Text font<br>
 bottomtext_font - Bottom Text font<br>
 novideotext_font - novideo Placeholder Text font<br>

## Dependencies

gst-plugins-good<br>
gst-plugins-base<br>
gst-plugin-fallbackswitch<br>
gst-libav<br>
pip3 gst package 