import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

Gst.init(None)

pipeline = Gst.Pipeline.new("h264flut_sound_wen")

udpsrc = Gst.ElementFactory.make("udpsrc", "udpsrc")
tsparse = Gst.ElementFactory.make("tsparse", "tsparse")
tsdemux = Gst.ElementFactory.make("tsdemux", "tsdemux")

queue_video = Gst.ElementFactory.make("queue", "queue_video")
h264parse = Gst.ElementFactory.make("h264parse", "h264parse")
avdec_h264 = Gst.ElementFactory.make("avdec_h264", "avdec_h264")
videoconvert = Gst.ElementFactory.make("videoconvert", "videoconvert")
autovideosink = Gst.ElementFactory.make("autovideosink", "autovideosink")

queue_audio = Gst.ElementFactory.make("queue", "queue_audio")
aacparse = Gst.ElementFactory.make("aacparse", "aacparse")
avdec_aac = Gst.ElementFactory.make("avdec_aac", "avdec_aac")
audioconvert = Gst.ElementFactory.make("audioconvert", "audioconvert")
audioresample = Gst.ElementFactory.make("audioresample", "audioresample")
alsasink = Gst.ElementFactory.make("alsasink", "alsasink")

udpsrc.set_property("port", 5000)
udpsrc.set_property("uri", "udp://0.0.0.0:5000")
queue_video.set_property("max-size-time", 5000000000)
queue_audio.set_property("max-size-time", 5000000000)

pipeline.add(udpsrc)
pipeline.add(tsparse)
pipeline.add(tsdemux)
pipeline.add(queue_video)
pipeline.add(h264parse)
pipeline.add(avdec_aac)
pipeline.add(avdec_h264)
pipeline.add(videoconvert)
pipeline.add(autovideosink)
pipeline.add(queue_audio)
pipeline.add(aacparse)
pipeline.add(audioconvert)
pipeline.add(audioresample)
pipeline.add(alsasink)

udpsrc.link(tsparse)
tsparse.link(tsdemux)

def on_pad_added(demux, pad, queue):
    name = pad.get_property("template").name_template
    print(name)
    if name.startswith("video"):
        pad.link(queue.get_static_pad("sink"))
    elif name.startswith("audio"):
        pad.link(queue.get_static_pad("sink"))

tsdemux.connect("pad-added", on_pad_added, queue_video)
tsdemux.connect("pad-added", on_pad_added, queue_audio)

queue_video.link(h264parse)
h264parse.link(avdec_h264)
avdec_h264.link(videoconvert)
videoconvert.link(autovideosink)

queue_audio.link(aacparse)
aacparse.link(avdec_aac)
avdec_aac.link(audioconvert)
audioconvert.link(audioresample)
audioresample.link(alsasink)

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