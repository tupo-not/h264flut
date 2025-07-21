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

## Some options in script
`toptext_str` - Top Text string value
<br>`bottomtext_str` - Bottom Text string value
<br>`novideotext_str` - No video text string value
<br>`toptext_font` - Top Text Font
<br>`bottomtext_font` - Bottom Text Font
<br>`novideotext_font` - No video Text Font
<br>`video_width` - Result video width
<br>`video_height` - Result video height
<br>`fallback_timeout` - Fallback switch timeout
<br>`listen_port` - UDP Listen port
<br>`listen_host` - UDP Listen host
<br>`server_listen_port` - TCP Server listen port
<br>`server_listen_host` - TCP Server listen host
<br>`nogui` - Use GUI?

## Dependencies

gst-plugins-good<br>
gst-plugins-base<br>
gst-plugin-fallbackswitch<br>
gst-libav<br>
pip3 gst package 