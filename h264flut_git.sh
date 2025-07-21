#!/bin/sh
gst-launch-1.0 udpsrc name=udpsrc13 port=5000 uri=udp://0.0.0.0:5000 ! capsfilter name=capsfilter2 \
! rtph264depay name=rtph264depay3 ! queue name=queue4 leaky=2 ! avdec_h264 name=avdec_h2645 \
! timeoverlay name=timeoverlay33 line-alignment=0 font-desc=arial auto-resize=true datetime-format=%t ! videoscale \
! "video/x-raw,width=800,height=600,pixel-aspect-ratio=(fraction)1/1" ! fallbackswitch name=fallbackswitch14 immediate-fallback=true timeout=5000000000 \
! imagefreeze name=imagefreeze10 is-live=true allow-replace=true \
! textoverlay name=bottomtext font-desc=impact text="No NSFW plz | Output resolution is 800x600 | running by CHANGEME and Gstreamer" auto-resize=false \
halignment=5 valignment=5 xpos=0.5 ypos=0.98 \
! textoverlay name=toptext font-desc=impact text="UDP A.B.C.D port EEEE | ONLY h264" auto-resize=false \
halignment=5 valignment=5 xpos=0.5 ypos=0.018 \
! autovideosink \
videotestsrc name=videotestsrc15 pattern=2 is-live=true ! videoscale \
! "video/x-raw,width=800,height=600,pixel-aspect-ratio=(fraction)1/1" \
! textoverlay name=novideotext silent=false text="NOVIDEO0)0))" halignment=1 scale-mode=0 valignment=4 line-alignment=1 font-desc=arial auto-resize=false ! fallbackswitch14. 
