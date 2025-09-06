import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import sys
import threading

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
resize_caps = "video/x-raw,width=800,height=600,pixel-aspect-ratio=(fraction)1/1,format=AYUV"
fallback_timeout = 1 # seconds
channels = 1

Gst.init(None)
pipeline = Gst.Pipeline.new("h264flut_multichannel_legacy")

class GstChannel:
    def __init__(self, ch_id: int):
        self.id = ch_id
        self.name_suffix = f"_ch{ch_id}"
        self.pad_lock = threading.Lock()
        self.udpsrc = self.make("udpsrc", "udp")
        self.iqueue = self.make("queue","iqueue")
        self.decodebin = self.make("decodebin3", "decodebin3")
        self.prerescale = self.make("videoconvertscale", "scale")
        self.rescale = self.make("capsfilter", "rescale")
        self.fallback = self.make("fallbackswitch", "fallback")
        self.imgfrz = self.make("imagefreeze", "imgfrz")
        self.toptext = self.make("textoverlay", "toptext")
        self.prerescale_blank = self.make("videoscale", "scale_blank")
        self.rescale_blank = self.make("capsfilter", "rescale_blank")
        self.testsrc = self.make("videotestsrc", "testsrc")
        self.novideotext = self.make("textoverlay", "novideotext")

        self.afallback = self.make("fallbackswitch", "afallback")
        self.atestsrc = self.make("audiotestsrc", "atestsrc")

        self.audioconvert = self.make("audioconvert", "audioconvert")
        self.audioresample = self.make("audioresample", "audioresample")

        self.video_pad_linked = False
        self.audio_pad_linked = False

    def make(self, factory_name, prefix):
        name = f"{prefix}{self.name_suffix}"
        element = Gst.ElementFactory.make(factory_name, name)
        if not element:
            print(f"Failed to create {factory_name}")
            sys.exit(1)
        return element

ch = [GstChannel(i) for i in range(channels)]
toptext = Gst.ElementFactory.make("textoverlay", "toptext")
bottomtext = Gst.ElementFactory.make("textoverlay", "bottomtext")
videomixer = Gst.ElementFactory.make("videomixer", "videomixer")
audiomixer = Gst.ElementFactory.make("audiomixer", "audiomixer")
convert = Gst.ElementFactory.make("videoconvertscale", "convert")

if nogui:
    mjpeg_encode = Gst.ElementFactory.make("avenc_mjpeg", "mjpeg_encode")
    output = Gst.ElementFactory.make("tcpserversink", "GUI_output")
    output.set_property("port", server_listen_port)
    output.set_property("host", server_listen_host)
else:
    output = Gst.ElementFactory.make("autovideosink", "GUI_output")
    aoutput = Gst.ElementFactory.make("alsasink", "audio_output")

def on_pad_added(demux, pad, channel):
    name = pad.get_property("template").name_template
    print(name)
    if name.startswith("video"):
        pad.link(channel.prerescale.get_static_pad("sink"))
    elif name.startswith("audio"):
        pad.link(channel.audioconvert.get_static_pad("sink"))

for i, channel in enumerate(ch):
    channel.udpsrc.set_property("port", listen_base_port + i)
    channel.udpsrc.set_property("uri", f"udp://{listen_host}:{listen_base_port + i}")
    channel.udpsrc.set_property("timeout", 5000000000)
    channel.decodebin.connect("pad-added", on_pad_added, channel)

    channel.rescale.set_property("caps", Gst.Caps.from_string(resize_caps))
    channel.rescale_blank.set_property("caps", Gst.Caps.from_string(resize_caps))

    channel.imgfrz.set_property("is-live", True)
    channel.imgfrz.set_property("allow-replace", True)

    channel.toptext.set_property("font-desc",toptext_font)
    channel.toptext.set_property("text",f"CH_{i}")
    channel.toptext.set_property("auto-resize",False)
    channel.toptext.set_property("halignment",5)
    channel.toptext.set_property("valignment",5)
    channel.toptext.set_property("xpos",0.8)
    channel.toptext.set_property("ypos",0.018)

    channel.fallback.set_property("immediate-fallback", True)
    channel.fallback.set_property("timeout", fallback_timeout * 1000000000)
    channel.testsrc.set_property("pattern", 2)
    channel.atestsrc.set_property("wave", 4)
    channel.testsrc.set_property("is-live", True)
    channel.atestsrc.set_property("is-live", True)


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

for channel in ch:
    for attr_name, element in vars(channel).items():
        if isinstance(element, Gst.Element) and element is not None:
            pipeline.add(element)

pipeline.add(convert)
pipeline.add(bottomtext)
pipeline.add(videomixer)
pipeline.add(audiomixer)
pipeline.add(output)

if not nogui:
    pipeline.add(aoutput)
else:
    pipeline.add(mjpeg_encode)

#link uall
for channel in ch:
    channel.udpsrc.link(channel.iqueue)
    channel.iqueue.link(channel.decodebin)
    channel.prerescale.link(channel.rescale)
    channel.rescale.link(channel.fallback)
    channel.fallback.link(channel.imgfrz)
    channel.imgfrz.link(channel.toptext)
    channel.toptext.link(videomixer)

    channel.audioconvert.link(channel.audioresample)
    channel.audioresample.link(channel.afallback)
    channel.afallback.link(audiomixer)

    channel.atestsrc.link(channel.afallback)
    channel.testsrc.link(channel.prerescale_blank)

    channel.prerescale_blank.link(channel.rescale_blank)
    channel.rescale_blank.link(channel.novideotext)
    channel.novideotext.link(channel.fallback)

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

try:
    ret = pipeline.set_state(Gst.State.PLAYING)
    loop = GLib.MainLoop()
    #bus.connect("message", handle_gstreamer_message, loop)
    loop.run()
    
except KeyboardInterrupt:
    print("\nStopping & dumping pipeline...")
    Gst.debug_bin_to_dot_file(pipeline, Gst.DebugGraphDetails.ALL, "pipeline")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    print("Cleaning up...")
    Gst.debug_bin_to_dot_file(pipeline, Gst.DebugGraphDetails.ALL, "pipeline")
    pipeline.set_state(Gst.State.NULL)