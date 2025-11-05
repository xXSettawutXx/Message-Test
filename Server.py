extends Node

var socket := WebSocketPeer.new()

func _ready():
    var url = "ws://localhost:8000"  # เปลี่ยนเป็น wss://xxxx.onrender.com เมื่อ deploy
    var err = socket.connect_to_url(url)
    if err != OK:
        print("❌ Failed to connect: ", err)
    else:
        print("✅ Connecting to server...")


func _process(delta):
    socket.poll()

    var state = socket.get_ready_state()

    if state == WebSocketPeer.STATE_OPEN:
        while socket.get_available_packet_count() > 0:
            var text = socket.get_packet().get_string_from_utf8()
            print("📩 Received:", text)
            _handle_message(text)

    elif state == WebSocketPeer.STATE_CLOSED:
        print("⚠️ WebSocket closed:", socket.get_close_code(), socket.get_close_reason())


func send_json(data: Dictionary):
    var msg = JSON.stringify(data)
    socket.send_text(msg)
    print("📤 Sent:", msg)


func _handle_message(msg: String):
    var json = JSON.parse_string(msg)
    if typeof(json) == TYPE_DICTIONARY:
        print("✅ Parsed server data:", json)
