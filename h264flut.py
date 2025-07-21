import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

toptext_str = "UDP A.B.C.D port EEEE | ONLY h264"
bottomtext_str = "No NSFW plz | Output resolution is 800x600 | running by CHANGEME and Gstreamer"
novideotext_str = "NOVIDEO0)0))"
toptext_font = "impact"
bottomtext_font = "impact"
novideotext_font = "arial"

resize_cups = "video/x-raw,width=800,height=600,pixel-aspect-ratio=(fraction)1/1"
fallback_timeout = 5 #seconds!11!!!!
listen_port = 5000
listen_host = "0.0.0.0"

Gst.init(None)

pipeline = Gst.Pipeline.new("h264flut")

#spawn uall
udp_src = Gst.ElementFactory.make("udpsrc","udp_src")
capsfilter = Gst.ElementFactory.make("capsfilter","capsfilter")
rtp_depay = Gst.ElementFactory.make("rtph264depay","rtp_depay")
input_queue = Gst.ElementFactory.make("queue","input_queue")
h264_decode = Gst.ElementFactory.make("avdec_h264","h264_decode")
input_time_overlay = Gst.ElementFactory.make("timeoverlay","input_time_overlay")
prerescale_input = Gst.ElementFactory.make("videoscale","prerescale_input")
rescale_input = Gst.ElementFactory.make("capsfilter","rescale_input")
novideo_switch = Gst.ElementFactory.make("fallbackswitch","novideo_switch")
last_input_frame_freeze = Gst.ElementFactory.make("imagefreeze","last_input_frame_freeze")
bottomtext = Gst.ElementFactory.make("textoverlay","bottomtext")
toptext = Gst.ElementFactory.make("textoverlay","toptext")
black_screen_src = Gst.ElementFactory.make("videotestsrc","black_screen_src")
prerescale_blank = Gst.ElementFactory.make("videoscale","prerescale_blank")
rescale_blank = Gst.ElementFactory.make("capsfilter","rescale_blank")
novideotext = Gst.ElementFactory.make("textoverlay","novideotext")

output = Gst.ElementFactory.make("autovideosink","GUI_output")

#setup uall
udp_src.set_property("port",listen_port)
udp_src.set_property("uri",f"udp://{listen_host}:{listen_port}")

input_queue.set_property("leaky",2)

input_time_overlay.set_property("line-alignment",0)
input_time_overlay.set_property("font-desc","arial")
input_time_overlay.set_property("auto-resize",True)
input_time_overlay.set_property("datetime-format","%t")

rescale_input.set_property("caps",Gst.Caps.from_string(resize_cups))

last_input_frame_freeze.set_property("is-live",True)
last_input_frame_freeze.set_property("allow-replace",True)

bottomtext.set_property("font-desc",bottomtext_font)
bottomtext.set_property("text",bottomtext_str)
bottomtext.set_property("auto-resize",False)
bottomtext.set_property("halignment",5)
bottomtext.set_property("valignment",5)
bottomtext.set_property("xpos",0.5)
bottomtext.set_property("ypos",0.98)

toptext.set_property("font-desc",toptext_font)
toptext.set_property("text",toptext_str)
toptext.set_property("auto-resize",False)
toptext.set_property("halignment",5)
toptext.set_property("valignment",5)
toptext.set_property("xpos",0.5)
toptext.set_property("ypos",0.018)

black_screen_src.set_property("pattern",2)
black_screen_src.set_property("is-live",True)

rescale_blank.set_property("caps",Gst.Caps.from_string(resize_cups))

novideotext.set_property("font-desc",novideotext_font)
novideotext.set_property("text",novideotext_str)
novideotext.set_property("auto-resize",False)
novideotext.set_property("halignment",5)
novideotext.set_property("valignment",5)
novideotext.set_property("xpos",0.5)
novideotext.set_property("ypos",0.5)
novideo_switch.set_property("immediate-fallback",True)
novideo_switch.set_property("timeout",fallback_timeout * 1000000000)

pipeline.add(udp_src)
pipeline.add(capsfilter)
pipeline.add(rtp_depay)
pipeline.add(input_queue)
pipeline.add(h264_decode)
pipeline.add(input_time_overlay)
pipeline.add(prerescale_input)
pipeline.add(rescale_input)
pipeline.add(novideo_switch)
pipeline.add(last_input_frame_freeze)
pipeline.add(bottomtext)
pipeline.add(toptext)
pipeline.add(black_screen_src)
pipeline.add(prerescale_blank)
pipeline.add(rescale_blank)
pipeline.add(novideotext)
pipeline.add(output)

udp_src.link(capsfilter)
capsfilter.link(rtp_depay)
rtp_depay.link(input_queue)
input_queue.link(h264_decode)
h264_decode.link(prerescale_input)
prerescale_input.link(rescale_input)
rescale_input.link(input_time_overlay)
input_time_overlay.link(novideo_switch)
novideo_switch.link(last_input_frame_freeze)
last_input_frame_freeze.link(toptext)
toptext.link(bottomtext)
bottomtext.link(output)
#input_time_overlay.link(output)

black_screen_src.link(prerescale_blank)
prerescale_blank.link(rescale_blank)
rescale_blank.link(novideotext)
novideotext.link(novideo_switch)

pipeline.set_state(Gst.State.PLAYING)

try:
    loop = GLib.MainLoop()
    loop.run()
except KeyboardInterrupt:
    print("\nStopping...")
finally:
    pipeline.set_state(Gst.State.NULL)
