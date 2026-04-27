import time
import threading
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

items_store = []
lock = threading.Lock()

@app.route('/health')
def health():
    return jsonify({"ok": True})

@app.route('/items/simple')
def items_simple():
    limit = request.args.get('limit', 15, type=int)
    min_money = request.args.get('min_money', 0, type=int)

    with lock:
        filtered = [it for it in items_store if it.get("money", 0) >= min_money]
        filtered.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        result = filtered[:limit]

    return jsonify({"ok": True, "items": result, "more": len(filtered) > limit})

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if not data:
        return "bad json", 400

    jobid = data.get("jobid") or data.get("server_id") or data.get("id")
    name = data.get("name") or data.get("pet_name") or data.get("pet")
    money = data.get("money") or data.get("cash_per_second") or data.get("cps")
    if not jobid or not name:
        return "missing jobid or name", 400

    data["jobid"] = jobid
    data["name"] = name
    data["money"] = int(money) if money else 0
    data["timestamp"] = time.time()

    with lock:
        items_store[:] = [it for it in items_store if it.get("jobid") != jobid]
        items_store.append(data)
        if len(items_store) > 50:
            items_store[:] = items_store[-50:]

    return "ok", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
