import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import configparser
config = configparser.ConfigParser()
config.read("config.ini")
import argparse 
parser = argparse.ArgumentParser()

parser.add_argument('-vw', required=False, type=int, help="Video Width")
parser.add_argument('-vh', required=False, type=int, help="Video Height")
parser.add_argument('--uport', required=False, type=int, help="UDP Listen port")
parser.add_argument('--uhost', required=False, type=str, help="UDP Listen host")
parser.add_argument('--watch_port', required=False, type=int, help="TCP Server Listen port")
parser.add_argument('--watch_host', required=False, type=str, help="TCP Server Listen host")
parser.add_argument('--nogui', required=False, type=bool, help="Use GUI?")
parser.add_argument('--toptext', required=False, type=str, help="Top Text String")
parser.add_argument('--bottomtext', required=False, type=str, help="Bottom Text String")
parser.add_argument('--novideotext', required=False, type=str, help="Novideo Text String")
parser.add_argument('--toptext_font', required=False, type=str, help="Top Text Font")
parser.add_argument('--bottomtext_font', required=False, type=str, help="Bottom Text Font")
parser.add_argument('--novideotext_font', required=False, type=str, help="Novideo Text Font")
parser.add_argument('-t', required=False, type=int, help="Fallback timeout(in seconds)")
args = parser.parse_args()
fallback_timeout = 5 #seconds!11!!!!

#apply uall
video_width = 800
video_height = 600
listen_port = 5000
listen_host = "0.0.0.0"
server_listen_port = 5001
server_listen_host = "0.0.0.0"
nogui = False

toptext_str = f"UDP {listen_host} port {listen_port} | ONLY h264"
bottomtext_str = f"No NSFW plz | Output resolution is {video_width}x{video_height} | running by CHANGEME and Gstreamer"
novideotext_str = "NOVIDEO0)0))"
toptext_font = "impact"
bottomtext_font = "impact"
novideotext_font = "arial"

if config:
    try:
        if config["Video"]["width"]: video_width = int(config["Video"]["width"])
        if config["Video"]["height"]: video_height = int(config["Video"]["height"])
        if config["Net"]["listen_port"]: listen_port = int(config["Net"]["listen_port"])
        if config["Net"]["listen_host"]: listen_host = config["Net"]["listen_host"]
        if config["Net"]["server_listen_port"]: server_listen_port = int(config["Net"]["server_listen_port"])
        if config["Net"]["server_listen_host"]: server_listen_host = config["Net"]["server_listen_host"]
        if config["Video"]["nogui"].lower() == 'y':
            nogui = True
        else:
            nogui = False
        if config["Text"]["toptext"]: toptext_str = config["Text"]["toptext"]
        if config["Text"]["bottomtext"]: bottomtext_str = config["Text"]["bottomtext"]
        if config["Text"]["novideotext"]: novideotext_str = config["Text"]["novideotext"]
        if config["Text"]["toptext_font"]: toptext_font = config["Text"]["toptext_font"]
        if config["Text"]["bottomtext_font"]: bottomtext_font = config["Text"]["bottomtext_font"]
        if config["Text"]["novideotext_font"]: novideotext_font = config["Text"]["novideotext_font"]
        if config["Video"]["fallback_timeout"]: fallback_timeout = int(config["Video"]["fallback_timeout"])
    except:
        pass
else:
    print("no config file :c")

try:
    if args.vw: video_width = args.vw
    if args.vh: video_height = args.vh
    if args.uport: listen_port = args.uport
    if args.uhost: listen_host = args.uhost
    if args.watch_port: server_listen_port = args.watch_port
    if args.watch_host: server_listen_host = args.watch_host
    if args.nogui: nogui = args.nogui
    if args.toptext: toptext_str = args.toptext
    if args.bottomtext: bottomtext_str = args.bottomtext
    if args.novideotext: novideotext_str = args.novideotext
    if args.toptext_font: toptext_font = args.toptext_font
    if args.bottomtext_font: bottomtext_font = args.bottomtext_font
    if args.novideotext_font: novideotext_font = args.novideotext_font
    if args.t: fallback_timeout = args.t
except:
    pass

Gst.init(None)
bottomtext_str.format()
toptext_str.format()
resize_cups = f"video/x-raw,width={video_width},height={video_height},pixel-aspect-ratio=(fraction)1/1"
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
last_in_pic_frz = Gst.ElementFactory.make("imagefreeze","last_in_pic_frz")
bottomtext = Gst.ElementFactory.make("textoverlay","bottomtext")
toptext = Gst.ElementFactory.make("textoverlay","toptext")
black_screen_src = Gst.ElementFactory.make("videotestsrc","black_screen_src")
prerescale_blank = Gst.ElementFactory.make("videoscale","prerescale_blank")
rescale_blank = Gst.ElementFactory.make("capsfilter","rescale_blank")
novideotext = Gst.ElementFactory.make("textoverlay","novideotext")

if nogui:
    mjpeg_encode = Gst.ElementFactory.make("avenc_mjpeg","mjpeg_encode")
    output = Gst.ElementFactory.make("tcpserversink","GUI_output")
else:
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

last_in_pic_frz.set_property("is-live",True)
last_in_pic_frz.set_property("allow-replace",True)

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
if nogui:
    output.set_property("port",server_listen_port)
    output.set_property("host",server_listen_host)

pipeline.add(udp_src)
pipeline.add(capsfilter)
pipeline.add(rtp_depay)
pipeline.add(input_queue)
pipeline.add(h264_decode)
pipeline.add(input_time_overlay)
pipeline.add(prerescale_input)
pipeline.add(rescale_input)
pipeline.add(novideo_switch)
pipeline.add(last_in_pic_frz)
pipeline.add(bottomtext)
pipeline.add(toptext)
pipeline.add(black_screen_src)
pipeline.add(prerescale_blank)
pipeline.add(rescale_blank)
pipeline.add(novideotext)
if nogui:
    pipeline.add(mjpeg_encode)
pipeline.add(output)

udp_src.link(capsfilter)
capsfilter.link(rtp_depay)
rtp_depay.link(input_queue)
input_queue.link(h264_decode)
h264_decode.link(prerescale_input)
prerescale_input.link(rescale_input)
rescale_input.link(input_time_overlay)
input_time_overlay.link(novideo_switch)
novideo_switch.link(last_in_pic_frz)
last_in_pic_frz.link(toptext)
toptext.link(bottomtext)

#TOPOLOGY
#udp_src > capfilter > rtp_depay > input_queue > h264_decode > 
#> prerescale_input > rescale_input > input_time_overlay >
#> novideo_switch > last_in_pic_frz > toptext >
if nogui:
    bottomtext.link(mjpeg_encode)
    mjpeg_encode.link(output) # toptext > mjpeg_encode > tcpserversink
else:
    bottomtext.link(output) # toptext > autovideosink

black_screen_src.link(prerescale_blank)
prerescale_blank.link(rescale_blank)
rescale_blank.link(novideotext)
novideotext.link(novideo_switch)
#ONE MORE TOPOLOGY
#black_screen_src > prerescale_blank > rescale_blank > novideotext

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
