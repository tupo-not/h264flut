import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

Gst.init(None)

pipeline = Gst.Pipeline.new("h264flut")

#spawn uall
udp_src = Gst.ElementFactory.make("udpsrc","udp_src")
capsfilter = Gst.ElementFactory.make("capsfilter","capsfilter")
rtp_depay = Gst.ElementFactory.make("rtph264depay","rtp_depay")
input_queue = Gst.ElementFactory.make("queue","input_queue")
h264_decode = Gst.ElementFactory.make("avdec_h264","h264_decode")
input_time_overlay = Gst.ElementFactory.make("timeoverlay","input_time_overlay")
rescale_input = Gst.ElementFactory.make("capsfilter","rescale_input")
novideo_switch = Gst.ElementFactory.make("fallbackswitch","novideo_switch")
last_input_frame_freeze = Gst.ElementFactory.make("imagefreeze","last_input_frame_freeze")
bottomtext = Gst.ElementFactory.make("textoverlay","bottomtext")
toptext = Gst.ElementFactory.make("textoverlay","toptext")
black_screen_src = Gst.ElementFactory.make("videotestsrc","black_screen_src")
rescale_blank = Gst.ElementFactory.make("capsfilter","rescale_blank")
novideotext = Gst.ElementFactory.make("textoverlay","novideotext")

output = Gst.ElementFactory.make("autovideosink","GUI_output")

#setup uall
udp_src.set_property("port",5000)
#udp_src.set_property("host","0.0.0.0")

input_queue.set_property("leaky",2)

input_time_overlay.set_property("line-alignment",0)
input_time_overlay.set_property("font-desc","arial")
input_time_overlay.set_property("auto-resize",True)
input_time_overlay.set_property("datetime-format","%t")

rescale_input.set_property("caps",Gst.Caps.from_string("video/x-raw,width=800,height=600,pixel-aspect-ratio=(fraction)1/1"))

last_input_frame_freeze.set_property("is-live",True)
last_input_frame_freeze.set_property("allow-replace",True)

bottomtext.set_property("font-desc","impact")
bottomtext.set_property("text","No NSFW plz | Output resolution is 800x600 | running by CHANGEME and Gstreamer")
bottomtext.set_property("auto-resize",False)
bottomtext.set_property("halignment",5)
bottomtext.set_property("valignment",5)
bottomtext.set_property("xpos",0.5)
bottomtext.set_property("ypos",0.98)

toptext.set_property("font-desc","impact")
toptext.set_property("text","UDP A.B.C.D port EEEE | ONLY h264")
toptext.set_property("auto-resize",False)
toptext.set_property("halignment",5)
toptext.set_property("valignment",5)
toptext.set_property("xpos",0.5)
toptext.set_property("ypos",0.018)

black_screen_src.set_property("pattern",2)
black_screen_src.set_property("is-live",True)

rescale_blank.set_property("caps",Gst.Caps.from_string("video/x-raw,width=800,height=600,pixel-aspect-ratio=(fraction)1/1"))

novideotext.set_property("font-desc","arial")
novideotext.set_property("text","NOVIDEO0)0))")
novideotext.set_property("auto-resize",False)
novideotext.set_property("halignment",5)
novideotext.set_property("valignment",5)
novideotext.set_property("xpos",0.5)
novideotext.set_property("ypos",0.5)

pipeline.add(udp_src)
pipeline.add(capsfilter)
pipeline.add(rtp_depay)
pipeline.add(input_queue)
pipeline.add(h264_decode)
pipeline.add(input_time_overlay)
pipeline.add(rescale_input)
pipeline.add(novideo_switch)
pipeline.add(last_input_frame_freeze)
pipeline.add(bottomtext)
pipeline.add(toptext)
pipeline.add(black_screen_src)
pipeline.add(rescale_blank)
pipeline.add(novideotext)
pipeline.add(output)

udp_src.link(capsfilter)
capsfilter.link(rtp_depay)
rtp_depay.link(input_queue)
input_queue.link(h264_decode)
h264_decode.link(input_time_overlay)
input_time_overlay.link(rescale_input)
rescale_input.link(novideo_switch)
novideo_switch.link(last_input_frame_freeze)
last_input_frame_freeze.link(toptext)
toptext.link(bottomtext)
bottomtext.link(output)

black_screen_src.link(rescale_blank)
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
