import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

listen_base_port = 5000
listen_host = "0.0.0.0"
server_listen_port = 5000
server_listen_host = "0.0.0.0"
nogui = False
bottomtext_str = f"No NSFW plz | running by CHANGEME and Gstreamer"
novideotext_str = "NOVIDEO0)0))"
toptext_font = "impact"
bottomtext_font = "impact"
novideotext_font = "arial"
resize_cups = f"video/x-raw,width=800,height=600,pixel-aspect-ratio=(fraction)1/1"
fallback_timeout = 1 #seconds!11!!!!

Gst.init(None)
pipeline = Gst.Pipeline.new("h264flut_4channel")
class GstChannel: #хигад's code
    def __init__(self, ch_id: int):
        self.id = ch_id
        self.name_suffix = f"_ch{ch_id}"
        self.udpsrc = self.make("udpsrc", "udp")
        self.cfilter = self.make("capsfilter", "cfilter")
        self.depay = self.make("rtph264depay", "depay")
        self.queue = self.make("queue", "que")
        self.decode = self.make("avdec_h264", "decode")
        self.scale = self.make("videoscale", "scale")
        self.rescale = self.make("capsfilter", "rescale")
        self.fallback = self.make("fallbackswitch", "fallback")
        self.imgfrz = self.make("imagefreeze", "imgfrz")
        self.toptext = self.make("textoverlay", "toptext")
        self.testsrc = self.make("videotestsrc", "testsrc")
        self.novideotext = self.make("textoverlay","novideotext")

    def make(self, factory_name, prefix):
        name = f"{prefix}{self.name_suffix}"
        return Gst.ElementFactory.make(factory_name, name)
    
#spawn uall
ch = [GstChannel(i) for i in range(9)]
toptext = Gst.ElementFactory.make("textoverlay","toptext")
bottomtext = Gst.ElementFactory.make("textoverlay","bottomtext")
videomixer = Gst.ElementFactory.make("videomixer","videomixer")
convert = Gst.ElementFactory.make("videoconvert","convert")

if nogui:
    mjpeg_encode = Gst.ElementFactory.make("avenc_mjpeg","mjpeg_encode")
    output = Gst.ElementFactory.make("tcpserversink","GUI_output")
    output.set_property("port",server_listen_port)
    output.set_property("host",server_listen_host)
else:
    output = Gst.ElementFactory.make("autovideosink","GUI_output")

#setup uall
i = 0
for channel in ch:
    i += 1
    channel.udpsrc.set_property("port",listen_base_port+(i-1))
    channel.udpsrc.set_property("uri",f"udp://{listen_host}:{listen_base_port+(i-1)}")
    channel.queue.set_property("leaky",2)
    channel.rescale.set_property("caps",Gst.Caps.from_string(resize_cups))
    channel.imgfrz.set_property("is-live",True)
    channel.imgfrz.set_property("allow-replace",True)
    channel.toptext.set_property("font-desc",toptext_font)
    channel.toptext.set_property("text",f"CH_{i-1}")
    channel.toptext.set_property("auto-resize",False)
    channel.toptext.set_property("halignment",5)
    channel.toptext.set_property("valignment",5)
    channel.toptext.set_property("xpos",0.8)
    channel.toptext.set_property("ypos",0.018)
    channel.fallback.set_property("immediate-fallback",True)
    channel.fallback.set_property("timeout",fallback_timeout * 1000000000)
    channel.testsrc.set_property("pattern",2)
    channel.testsrc.set_property("is-live",True)
    channel.novideotext.set_property("font-desc",novideotext_font)
    channel.novideotext.set_property("text",novideotext_str)
    channel.novideotext.set_property("auto-resize",False)
    channel.novideotext.set_property("halignment",5)
    channel.novideotext.set_property("valignment",5)
    channel.novideotext.set_property("xpos",0.5)
    channel.novideotext.set_property("ypos",0.5)


bottomtext.set_property("font-desc",bottomtext_font)
bottomtext.set_property("text",bottomtext_str)
bottomtext.set_property("auto-resize",False)
bottomtext.set_property("halignment",5)
bottomtext.set_property("valignment",5)
bottomtext.set_property("xpos",0.5)
bottomtext.set_property("ypos",0.98)
pad0 = videomixer.get_request_pad("sink_%u")
pad1 = videomixer.get_request_pad("sink_%u")
pad2 = videomixer.get_request_pad("sink_%u")
pad3 = videomixer.get_request_pad("sink_%u")
pad4 = videomixer.get_request_pad("sink_%u")
pad5 = videomixer.get_request_pad("sink_%u")
pad6 = videomixer.get_request_pad("sink_%u")
pad7 = videomixer.get_request_pad("sink_%u")
pad8 = videomixer.get_request_pad("sink_%u")

pad0.set_property("xpos", 0)
pad0.set_property("ypos", 0)
pad1.set_property("xpos", 800)
pad1.set_property("ypos", 0)
pad2.set_property("xpos", 1600)
pad2.set_property("ypos", 0)

pad3.set_property("xpos", 0)
pad3.set_property("ypos", 600)
pad4.set_property("xpos", 800)
pad4.set_property("ypos", 600)
pad5.set_property("xpos", 1600)
pad5.set_property("ypos", 600)

pad6.set_property("xpos", 0)
pad6.set_property("ypos", 1200)
pad7.set_property("xpos", 800)
pad7.set_property("ypos", 1200)
pad8.set_property("xpos", 1600)
pad8.set_property("ypos", 1200)

#add uall
for channel in ch:
    pipeline.add(channel.udpsrc)
    pipeline.add(channel.cfilter)
    pipeline.add(channel.depay)
    pipeline.add(channel.queue)
    pipeline.add(channel.decode)
    pipeline.add(channel.scale)
    pipeline.add(channel.rescale)
    pipeline.add(channel.fallback)
    pipeline.add(channel.imgfrz)
    pipeline.add(channel.toptext)
    pipeline.add(channel.testsrc)
    pipeline.add(channel.novideotext)

pipeline.add(convert)
pipeline.add(bottomtext)
pipeline.add(videomixer)

if nogui:
    pipeline.add(mjpeg_encode)
pipeline.add(output)

for channel in ch: #LINK CHANNELS~
    channel.udpsrc.link(channel.cfilter)
    channel.cfilter.link(channel.depay)
    channel.depay.link(channel.queue)
    channel.queue.link(channel.decode)
    channel.decode.link(channel.fallback) 
    channel.testsrc.link(channel.novideotext)
    channel.novideotext.link(channel.fallback)
    channel.fallback.link(channel.scale)
    channel.scale.link(channel.rescale)
    channel.rescale.link(channel.imgfrz)
    channel.imgfrz.link(channel.toptext)
    channel.toptext.link(videomixer)
    
if nogui:
    videomixer.link(convert)
    convert.link(bottomtext)
    bottomtext.link(mjpeg_encode)
    mjpeg_encode.link(output)
else:
    videomixer.link(convert)
    convert.link(bottomtext)
    bottomtext.link(output)


def handle_gstreamer_message(_bus: Gst.Bus, message: Gst.Message, loop: GLib.MainLoop):
    message_type = message.type
    if message_type == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        print(err, debug)

try:
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    pipeline.set_state(Gst.State.PLAYING)
    loop = GLib.MainLoop()
    bus.connect('message', handle_gstreamer_message, loop)
    loop.run()
except KeyboardInterrupt:
    print("\nStopping...")
except GLib.Error as e:
    print(e)
finally:
    pipeline.set_state(Gst.State.NULL)
