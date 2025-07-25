import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

listen_base_port = 5000
listen_host = "0.0.0.0"
server_listen_port = 5000
server_listen_host = "::"
nogui = True
bottomtext_str = "No NSFW plz | running by CHANGEME and Gstreamer"
novideotext_str = "NOVIDEO0)0))"
toptext_font = "impact"
bottomtext_font = "impact"
novideotext_font = "arial"
resize_cups = "video/x-raw,width=800,height=600,pixel-aspect-ratio=(fraction)1/1"
h264_caps = "application/x-rtp,media=video,encoding-name=H264,payload=96"
fallback_timeout = 1 #seconds!11!!!!
channels = 9

Gst.init(None)
pipeline = Gst.Pipeline.new("h264flut_multichannel")

class GstChannel:
    def __init__(self, ch_id: int):
        self.id = ch_id
        self.name_suffix = f"_ch{ch_id}"
        self.udpsrc = self.make("udpsrc", "udp")
        self.cfilter = self.make("capsfilter", "cfilter")
        self.depay = self.make("rtph264depay", "depay")
        self.parse = self.make("h264parse", "parse")
        self.queue = self.make("queue", "que")
        self.decode = self.make("avdec_h264", "decode")
        self.scale = self.make("videoconvertscale", "scale")
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
ch = [GstChannel(i) for i in range(channels)]
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
    channel.cfilter.set_property("caps", Gst.Caps.from_string(h264_caps))
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

#silly matrix
cols = int(channels ** 0.5) + (1 if channels ** 0.5 % 1 else 0)
rows = (channels + cols - 1) // cols
pads = []

for i in range(channels):
    pad = videomixer.get_request_pad("sink_%u")
    pads.append(pad)
    x = (i % cols) * 800
    y = (i // cols) * 600
    pad.set_property("xpos", x)
    pad.set_property("ypos", y)

#add uall
for channel in ch:
    attributes = vars(channel)
    for attr_name, element in attributes.items():
        if isinstance(element, Gst.Element):
            pipeline.add(element)

pipeline.add(convert)
pipeline.add(bottomtext)
pipeline.add(videomixer)
pipeline.add(output)

if nogui:
    pipeline.add(mjpeg_encode)

for channel in ch:
    channel.udpsrc.link(channel.cfilter)
    channel.cfilter.link(channel.depay)
    channel.depay.link(channel.parse)
    channel.parse.link(channel.queue)
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


def handle_gstreamer_message(_bus: Gst.Bus, message: Gst.Message, loop: GLib.MainLoop): #debug
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
