from flask import Flask, render_template, jsonify
from scapy.all import sniff, IP, TCP, UDP
import threading

app = Flask(__name__)

packets = []
capturing = False  # Initially not capturing

def packet_callback(packet):
    if IP in packet:
        ip_layer = packet[IP]
        packet_info = {
            "src_ip": ip_layer.src,
            "dst_ip": ip_layer.dst,
            "protocol": ip_layer.proto,
            "ttl": getattr(ip_layer, "ttl", "N/A"),
            "ip_version": getattr(ip_layer, "version", "N/A"),
            "ip_len": getattr(ip_layer, "len", "N/A"),
        }

        if TCP in packet:
            tcp_layer = packet[TCP]
            packet_info.update({
                "src_port": tcp_layer.sport,
                "dst_port": tcp_layer.dport,
                "payload": str(tcp_layer.payload),
                "seq": getattr(tcp_layer, "seq", "N/A"),
                "ack": getattr(tcp_layer, "ack", "N/A"),
                # Convert flags to string
                "flags": str(getattr(tcp_layer, "flags", "N/A")),
            })
        elif UDP in packet:
            udp_layer = packet[UDP]
            packet_info.update({
                "src_port": udp_layer.sport,
                "dst_port": udp_layer.dport,
                "payload": str(udp_layer.payload),
            })

        packets.append(packet_info)

def stop_filter(packet):
    return not capturing

def start_sniffing():
    try:
        sniff(filter="ip", prn=packet_callback, store=0, stop_filter=stop_filter)
    except Exception as e:
        print("Error in sniffing:", e)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/packets')
def get_packets():
    return jsonify(packets)

@app.route('/stop')
def stop_capture():
    global capturing
    capturing = False
    return jsonify({"status": "stopped"})

@app.route('/start')
def start_capture():
    global capturing
    if not capturing:
        capturing = True
        threading.Thread(target=start_sniffing, daemon=True).start()
        return jsonify({"status": "started"})
    return jsonify({"status": "already capturing"})

if __name__ == '__main__':
    app.run(debug=True)
