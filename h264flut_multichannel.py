import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

listen_base_port = 5000
listen_host = "0.0.0.0"
server_listen_port = 5000
server_listen_host = "::"
nogui = False
bottomtext_str = "No NSFW plz | running by CHANGEME and Gstreamer"
novideotext_str = "NOVIDEO0)0))"
toptext_font = "impact"
bottomtext_font = "impact"
novideotext_font = "arial"
resize_cups = "video/x-raw,width=800,height=600,pixel-aspect-ratio=(fraction)1/1"
fallback_timeout = 1 #seconds!11!!!!
channels = 1

Gst.init(None)
pipeline = Gst.Pipeline.new("h264flut_multichannel")

class GstChannel:
    def __init__(self, ch_id: int):
        self.id = ch_id
        self.name_suffix = f"_ch{ch_id}"
        self.udpsrc = self.make("udpsrc", "udp")
        self.tsparse = self.make("tsparse", "tsparse")
        self.tsdemux = self.make("tsdemux", "tsdemux")
        self.vqueue = self.make("queue", "que")
        self.h264parse = self.make("h264parse", "h264parse")
        self.h264dec = self.make("avdec_h264", "h264dec")
        self.scale = self.make("videoconvertscale", "scale")
        self.rescale = self.make("capsfilter", "rescale")
        self.fallback = self.make("fallbackswitch", "fallback")
        self.imgfrz = self.make("imagefreeze", "imgfrz")
        self.toptext = self.make("textoverlay", "toptext")
        self.testsrc = self.make("videotestsrc", "testsrc")
        self.novideotext = self.make("timeoverlay","novideotext")

        self.aqueue = self.make("queue","aqueue")
        self.aacparse = self.make("aacparse","aacparse")
        self.aac_dec = self.make("avdec_aac","avdec_aac")
        self.audioconvert = self.make("audioconvert","audioconvert")
        self.audioresample = self.make("audioresample","audioresample")
        self.afallback = self.make("fallbackswitch", "afallback")
        self.atestsrc = self.make("audiotestsrc", "atestsrc")

    def make(self, factory_name, prefix):
        name = f"{prefix}{self.name_suffix}"
        return Gst.ElementFactory.make(factory_name, name)
    
#spawn uall
ch = [GstChannel(i) for i in range(channels)]
toptext = Gst.ElementFactory.make("textoverlay","toptext")
bottomtext = Gst.ElementFactory.make("textoverlay","bottomtext")
videomixer = Gst.ElementFactory.make("videomixer","videomixer")
audiomixer = Gst.ElementFactory.make("audiomixer","audiomixer")
convert = Gst.ElementFactory.make("videoconvert","convert")

if nogui:
    mjpeg_encode = Gst.ElementFactory.make("avenc_mjpeg","mjpeg_encode")
    output = Gst.ElementFactory.make("tcpserversink","GUI_output")
    output.set_property("port",server_listen_port)
    output.set_property("host",server_listen_host)
else:
    output = Gst.ElementFactory.make("autovideosink","GUI_output")
    aoutput = Gst.ElementFactory.make("autoaudiosink","audio_output")

#setup uall
def on_pad_added(demux, pad, queue):
    name = pad.get_property("template").name_template
    print(name)
    if name.startswith("video"):
        pad.link(queue.get_static_pad("sink"))
    elif name.startswith("audio"):
        pad.link(queue.get_static_pad("sink"))

i = 0
for channel in ch:
    i += 1
    channel.udpsrc.set_property("port",listen_base_port+(i-1))
    channel.udpsrc.set_property("uri",f"udp://{listen_host}:{listen_base_port+(i-1)}")
 #   channel.vqueue.set_property("leaky",2)
 #   channel.aqueue.set_property("leaky",2)
    channel.vqueue.set_property("max-size-time", 5000000000)
    channel.aqueue.set_property("max-size-time", 5000000000)
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
    #channel.novideotext.set_property("text",novideotext_str)
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
pipeline.add(audiomixer)
pipeline.add(output)
pipeline.add(aoutput)

if nogui:
    pipeline.add(mjpeg_encode)

#link uall
for channel in ch:
    channel.tsdemux.connect("pad-added", on_pad_added, channel.vqueue)
    channel.tsdemux.connect("pad-added", on_pad_added, channel.aqueue)
    channel.udpsrc.link(channel.tsparse)
    channel.tsparse.link(channel.tsdemux)
    #channel.tsdemux.link(channel.parse)
    channel.vqueue.link(channel.h264parse)
    channel.h264parse.link(channel.h264dec)
    channel.h264dec.link(channel.fallback) 
    channel.testsrc.link(channel.novideotext)
    channel.novideotext.link(channel.fallback)
    channel.fallback.link(channel.scale)
    channel.scale.link(channel.rescale)
    channel.rescale.link(channel.imgfrz)
    channel.imgfrz.link(channel.toptext)
    channel.toptext.link(videomixer)

    channel.aqueue.link(channel.aacparse)
    channel.aacparse.link(channel.aac_dec)
    channel.aac_dec.link(channel.audioconvert)
    channel.audioconvert.link(channel.afallback)
    #channel.audioresample.link(channel.afallback)
    channel.afallback.link(audiomixer)
    channel.atestsrc.link(channel.afallback)
    
if nogui:
    videomixer.link(convert)
    convert.link(bottomtext)
    bottomtext.link(mjpeg_encode)
    mjpeg_encode.link(output)
else:
    videomixer.link(convert)
    convert.link(bottomtext)
    bottomtext.link(output)
    audiomixer.link(aoutput)


def handle_gstreamer_message(bus, message, loop):
    t = message.type
    if t == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        print(f"Error: {err}, {debug}")
        loop.quit()
    elif t == Gst.MessageType.EOS:
        print("End of stream")
        loop.quit()
    elif t == Gst.MessageType.STATE_CHANGED:
        old, new, pending = message.parse_state_changed()
        print(f"State changed from {old} to {new}")
    return True


try:
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    pipeline.set_state(Gst.State.PLAYING)
    loop = GLib.MainLoop()
    bus.connect("message", handle_gstreamer_message, loop)
    Gst.debug_bin_to_dot_file_with_ts(pipeline, Gst.DebugGraphDetails.ALL, "pipeline")
    #Gst.debug_set_active(False)
    #Gst.debug_set_default_threshold(4)
    loop.run()
except KeyboardInterrupt:
    print("\nStopping...")
except GLib.Error as e:
    print(e)
finally:
    pipeline.set_state(Gst.State.NULL)
