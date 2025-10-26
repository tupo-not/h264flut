import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import argparse
import configparser
import sys

# ====== Defaults ======
DEFAULTS = {
    "listen_base_port": 5000,
    "listen_host": "0.0.0.0",
    "server_listen_port": 5000,
    "server_listen_host": "::",
    "nogui": False,
    "bottomtext_str": "No NSFW plz | running by CHANGEME, God's word and Gstreamer",
    "novideotext_str": "NOVIDEO0)0))",
    "toptext_font": "impact",
    "bottomtext_font": "impact",
    "novideotext_font": "arial",
    "resize_caps": "video/x-raw,width=800,height=600,pixel-aspect-ratio=(fraction)1/1,format=AYUV",
    "fallback_timeout": 1,
    "channels": 9
}

#Config
config = configparser.ConfigParser()
config.read("config.ini")

def get_config_option(section, key):
    try:
        if section in config and key in config[section]:
            val = config[section][key]
            # типизация
            if key in ["nogui"]:
                return config[section].getboolean(key)
            elif key in ["listen_base_port", "server_listen_port", "channels"]:
                return config[section].getint(key)
            elif key in ["fallback_timeout"]:
                return config[section].getfloat(key)
            return val
    except Exception as e:
        print(f"Error reading config [{section}] {key}: {e}")
    return DEFAULTS[key]

#CLI
parser = argparse.ArgumentParser()
parser.add_argument("--gui", action="store_false", help="GUI mode")
parser.add_argument("--listen-base-port", type=int, help="Base UDP port")
parser.add_argument("--server-listen-port", type=int, help="Server port")
parser.add_argument("--channels", type=int, help="Number of channels")
parser.add_argument("--bottomtext", type=str, help="Bottom text overlay")
parser.add_argument("--novideotext", type=str, help="Text when no video")
args = parser.parse_args()

listen_base_port = args.listen_base_port or get_config_option("general", "listen_base_port")
listen_host = get_config_option("general", "listen_host")
server_listen_port = args.server_listen_port or get_config_option("general", "server_listen_port")
server_listen_host = get_config_option("general", "server_listen_host")
nogui = args.gui or get_config_option("general", "nogui")
bottomtext_str = args.bottomtext or get_config_option("text", "bottomtext_str")
novideotext_str = args.novideotext or get_config_option("text", "novideotext_str")
toptext_font = get_config_option("text", "toptext_font")
bottomtext_font = get_config_option("text", "bottomtext_font")
novideotext_font = get_config_option("text", "novideotext_font")
resize_caps = get_config_option("video", "resize_caps")
fallback_timeout = get_config_option("general", "fallback_timeout")
channels = args.channels or get_config_option("general", "channels")

Gst.init(None)
pipeline = Gst.Pipeline.new("h264flut_multichannel")

class GstChannel:
    def __init__(self, ch_id: int):
        self.id = ch_id
        self.name_suffix = f"_ch{ch_id}"

        # Video
        self.udpsrc = self.make("udpsrc", "udp")
        self.iqueue = self.make("queue","iqueue")
        self.tsparse = self.make("tsparse", "tsparse")
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
        self.vqueue = self.make("queue", "vqueue")
        self.voutqueue = self.make("queue", "voutqueue")

        # Audio
        self.audioconvert = self.make("audioconvert", "audioconvert")
        self.audioresample = self.make("audioresample", "audioresample")
        self.afallback = self.make("fallbackswitch", "afallback")
        self.atestsrc = self.make("audiotestsrc", "atestsrc")
        self.audioqueue = self.make("queue", "audioqueue")
        self.aacenc = self.make("faac", "output_aac_enc")
        self.aoutqueue = self.make("queue", "aoutqueue")
        self.ainqueue = self.make("queue", "ainqueue")

    def make(self, factory_name, prefix):
        name = f"{prefix}{self.name_suffix}"
        element = Gst.ElementFactory.make(factory_name, name)
        if not element:
            print(f"Failed to create {factory_name}")
            sys.exit(1)
        return element

ch = [GstChannel(i) for i in range(channels)]

videomixer = Gst.ElementFactory.make("videomixer", "videomixer")
audiomixer = Gst.ElementFactory.make("audiomixer", "audiomixer")
convert = Gst.ElementFactory.make("videoconvertscale", "convert")

if nogui:
    h264_enc = Gst.ElementFactory.make("openh264enc", "h264_enc")
    aq1 = Gst.ElementFactory.make("queue", "aq1")
    vq1 = Gst.ElementFactory.make("queue", "vq1")
    aq2 = Gst.ElementFactory.make("queue", "aq2")
    vq2 = Gst.ElementFactory.make("queue", "vq2")
    aac_enc = Gst.ElementFactory.make("faac", "aac_enc")
    mpegts_mux = Gst.ElementFactory.make("mpegtsmux", "mpegts_mux")
    output = Gst.ElementFactory.make("tcpserversink", "nogui_output")
    output.set_property("port", server_listen_port)
    output.set_property("host", server_listen_host)
else:
    output = Gst.ElementFactory.make("autovideosink", "GUI_output")
    aoutput = Gst.ElementFactory.make("alsasink", "audio_output")

def on_pad_added(demux, pad, channel):
    if pad.is_linked():
        return
    caps = pad.get_current_caps()
    if not caps:
        caps = pad.query_caps(None)
    if caps.to_string().startswith("video"):
        pad.link(channel.prerescale.get_static_pad("sink"))
    elif caps.to_string().startswith("audio"):
        pad.link(channel.audioconvert.get_static_pad("sink"))

for i, channel in enumerate(ch):
    channel.udpsrc.set_property("port", listen_base_port + i)
    channel.udpsrc.set_property("timeout", 5000000000)
    channel.ainqueue.set_property("leaky", 2)
    channel.aoutqueue.set_property("leaky", 1)
    channel.vqueue.set_property("leaky", 1)
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
    channel.testsrc.set_property("is-live", True)
    channel.atestsrc.set_property("wave", 4)
    channel.atestsrc.set_property("is-live", True)

    channel.novideotext.set_property("font-desc",novideotext_font)
    channel.novideotext.set_property("text",novideotext_str)
    channel.novideotext.set_property("auto-resize",False)
    channel.novideotext.set_property("halignment",5)
    channel.novideotext.set_property("valignment",5)
    channel.novideotext.set_property("xpos",0.5)
    channel.novideotext.set_property("ypos",0.5)

bottomtext = Gst.ElementFactory.make("textoverlay", "bottomtext")
bottomtext.set_property("font-desc",bottomtext_font)
bottomtext.set_property("text",bottomtext_str)
bottomtext.set_property("auto-resize",False)
bottomtext.set_property("halignment",5)
bottomtext.set_property("valignment",5)
bottomtext.set_property("xpos",0.5)
bottomtext.set_property("ypos",0.98)
if nogui:
    vq1.set_property("leaky", 2)
    vq2.set_property("leaky", 2)
    aq1.set_property("leaky", 2)
    aq2.set_property("leaky", 2)

cols = int(channels ** 0.5) + (1 if channels ** 0.5 % 1 else 0)
for i in range(channels):
    pad = videomixer.get_request_pad("sink_%u")
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
    pipeline.add(mpegts_mux)
    pipeline.add(h264_enc)
    pipeline.add(aac_enc)
    pipeline.add(vq1)
    pipeline.add(vq2)

# Линки
for channel in ch:
    channel.udpsrc.link(channel.iqueue)
    channel.iqueue.link(channel.tsparse)
    channel.tsparse.link(channel.decodebin)

    channel.prerescale.link(channel.rescale)
    channel.rescale.link(channel.fallback)
    channel.fallback.link(channel.imgfrz)
    channel.imgfrz.link(channel.vqueue)
    channel.vqueue.link(channel.toptext)
    channel.toptext.link(videomixer)

    channel.audioconvert.link(channel.audioqueue)
    channel.audioqueue.link(channel.audioresample)
    channel.audioresample.link(channel.afallback)
    channel.atestsrc.link(channel.afallback)
    
    channel.testsrc.link(channel.prerescale_blank)
    channel.prerescale_blank.link(channel.rescale_blank)
    channel.rescale_blank.link(channel.novideotext)
    channel.novideotext.link(channel.fallback)

    if nogui:
        pipeline.remove(audiomixer)
        channel.afallback.link(channel.aacenc)
        channel.aacenc.link(channel.aoutqueue)
        channel.aoutqueue.link(mpegts_mux)
    else:
        channel.afallback.link(audiomixer)

if nogui:
    videomixer.link(convert)
    convert.link(bottomtext)
    bottomtext.link(h264_enc)
    h264_enc.link(vq1)
    vq1.link(mpegts_mux)
    mpegts_mux.link(vq2)
    vq2.link(output)
else:
    videomixer.link(convert)
    convert.link(bottomtext)
    bottomtext.link(output)
    audiomixer.link(aoutput)

try:
    pipeline.set_state(Gst.State.PLAYING)
    loop = GLib.MainLoop()
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
