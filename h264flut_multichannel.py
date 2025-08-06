import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import sys
import threading

# Конфигурация
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
resize_caps = "video/x-raw,width=800,height=600,pixel-aspect-ratio=(fraction)1/1"
fallback_timeout = 1  # seconds
channels = 9

Gst.init(None)
pipeline = Gst.Pipeline.new("h264flut_multichannel")

class GstChannel:
    def __init__(self, ch_id: int):
        self.id = ch_id
        self.name_suffix = f"_ch{ch_id}"
        self.pad_lock = threading.Lock()
        self.udpsrc = self.make("udpsrc", "udp")
        self.tsparse = self.make("tsparse", "tsparse")
        self.tsdemux = self.make("tsdemux", "tsdemux")
        self.vqueue = self.make("queue", "vqueue")
        self.h264parse = self.make("h264parse", "h264parse")
        self.h264dec = self.make("avdec_h264", "h264dec")
        self.prerescale = self.make("videoconvertscale", "scale")
        self.rescale = self.make("capsfilter", "rescale")
        self.fallback = self.make("fallbackswitch", "fallback")
        self.imgfrz = self.make("imagefreeze", "imgfrz")
        self.toptext = self.make("textoverlay", "toptext")

        self.testsrc = self.make("videotestsrc", "testsrc")
        self.novideotext = self.make("textoverlay", "novideotext")
        self.afallback = self.make("fallbackswitch", "afallback")
        self.atestsrc = self.make("audiotestsrc", "atestsrc")
        
        self.aqueue = self.make("queue", "aqueue")
        self.aacparse = self.make("aacparse", "aacparse")
        self.aac_dec = self.make("avdec_aac", "avdec_aac")
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
    aoutput = Gst.ElementFactory.make("autoaudiosink", "audio_output")

def on_pad_added(demux, pad, channel):
    with channel.pad_lock:
        pad_name = pad.get_name()
        pad_caps = pad.get_current_caps()
        
        if pad_caps:
            structure = pad_caps.get_structure(0)
            name = structure.get_name()
        else:
            template = pad.get_property("template")
            name = template.name_template if template else ""
        
        print(f"New pad: {pad_name}, type: {name}")
        
        if "video" in pad_name and not channel.video_pad_linked:
            sink_pad = channel.vqueue.get_static_pad("sink")
            if sink_pad and not sink_pad.is_linked():
                result = pad.link(sink_pad)
                if result == Gst.PadLinkReturn.OK:
                    channel.video_pad_linked = True
                    print(f"Successfully linked video pad for channel {channel.id}")
                else:
                    print(f"Failed to link video pad: {result}")
                    
        elif "audio" in pad_name and not channel.audio_pad_linked:
            sink_pad = channel.aqueue.get_static_pad("sink")
            if sink_pad and not sink_pad.is_linked():
                result = pad.link(sink_pad)
                if result == Gst.PadLinkReturn.OK:
                    channel.audio_pad_linked = True
                    print(f"Successfully linked audio pad for channel {channel.id}")
                else:
                    print(f"Failed to link audio pad: {result}")

for i, channel in enumerate(ch):
    channel.udpsrc.set_property("port", listen_base_port + i)
    channel.udpsrc.set_property("uri", f"udp://{listen_host}:{listen_base_port + i}")
    channel.udpsrc.set_property("buffer-size", 2097152)  # 2MB
    channel.udpsrc.set_property("timeout", 5000000000)  # 5 seconds
    channel.tsdemux.connect("pad-added", on_pad_added, channel)
    channel.vqueue.set_property("max-size-buffers", 0)
    channel.vqueue.set_property("max-size-bytes", 0)
    channel.vqueue.set_property("max-size-time", 2000000000)  # 2 seconds
    channel.vqueue.set_property("leaky", 2)
    channel.aqueue.set_property("max-size-buffers", 0)
    channel.aqueue.set_property("max-size-bytes", 0)
    channel.aqueue.set_property("max-size-time", 2000000000)
    channel.aqueue.set_property("leaky", 2)
    channel.h264parse.set_property("config-interval", -1)
    channel.h264parse.set_property("disable-passthrough", True)
    channel.rescale.set_property("caps", Gst.Caps.from_string(resize_caps))
    channel.imgfrz.set_property("is-live", True)
    channel.imgfrz.set_property("allow-replace", True)
    channel.toptext.set_property("font-desc",toptext_font)
    channel.toptext.set_property("text",f"CH_{i-1}")
    channel.toptext.set_property("auto-resize",False)
    channel.toptext.set_property("halignment",5)
    channel.toptext.set_property("valignment",5)
    channel.toptext.set_property("xpos",0.8)
    channel.toptext.set_property("ypos",0.018)
    channel.fallback.set_property("immediate-fallback", True)
    channel.fallback.set_property("timeout", fallback_timeout * 1000000000)
    channel.testsrc.set_property("pattern", 2)
    channel.testsrc.set_property("is-live", True)
    channel.novideotext.set_property("font-desc",novideotext_font)
    channel.novideotext.set_property("text",novideotext_str)
    channel.novideotext.set_property("auto-resize",False)
    channel.novideotext.set_property("halignment",5)
    channel.novideotext.set_property("valignment",5)
    channel.novideotext.set_property("xpos",0.5)
    channel.novideotext.set_property("ypos",0.5)
    channel.atestsrc.set_property("is-live", True)
    channel.atestsrc.set_property("wave", 4)  # silence

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

# Add elements to pipeline
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
    # Input chain
    channel.udpsrc.link(channel.tsparse)
    channel.tsparse.link(channel.tsdemux)
    
    # Video chain
    channel.vqueue.link(channel.h264parse)
    channel.h264parse.link(channel.h264dec)
    channel.h264dec.link(channel.fallback)
    channel.fallback.link(channel.prerescale)
    channel.prerescale.link(channel.rescale)
    channel.rescale.link(channel.imgfrz)
    channel.imgfrz.link(channel.toptext)
    channel.toptext.link(videomixer)

    channel.aqueue.link(channel.aacparse)
    channel.aacparse.link(channel.aac_dec)
    channel.aac_dec.link(channel.audioconvert)
    channel.audioconvert.link(channel.audioresample)
    channel.audioresample.link(channel.afallback)
    channel.afallback.link(audiomixer)

    channel.atestsrc.link(channel.afallback)
    channel.testsrc.link(channel.novideotext)
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

def handle_gstreamer_message(bus, message, loop):
    t = message.type
    if t == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        print(f"Error from {message.src.get_name()}: {err}, {debug}")
        loop.quit()
    elif t == Gst.MessageType.EOS:
        print("End of stream")
        loop.quit()
    elif t == Gst.MessageType.WARNING:
        warn, debug = message.parse_warning()
        print(f"Warning from {message.src.get_name()}: {warn}, {debug}")
    return True

try:
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    
    print("Starting pipeline...")
    ret = pipeline.set_state(Gst.State.PLAYING)
    
    if ret == Gst.StateChangeReturn.FAILURE:
        print("Failed to start pipeline")
        sys.exit(1)
    
    loop = GLib.MainLoop()
    bus.connect("message", handle_gstreamer_message, loop)
    
    print("Pipeline running...")
    loop.run()
    
except KeyboardInterrupt:
    print("\nStopping...")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    print("Cleaning up...")
    pipeline.set_state(Gst.State.NULL)