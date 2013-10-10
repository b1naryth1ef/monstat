from flask import Flask, render_template
from flask_sockets import Sockets

from master import Master

import thread, time, json
import datetime

app = Flask(__name__)
sockets = Sockets(app)

dthandler = lambda obj: obj.isoformat() if isinstance(obj, datetime.datetime) else None
m = Master()

test = {
    "graphs": [{
        "id": "#redis",
        "series": [
            {
                "name": "test",
                "data": [
                    [datetime.datetime.now(), 5],
                ]
            }
        ]
    }]
}

def get_stats():
    test = {"graphs": []}

    for stat in m.graphs.stats:
        print "Graphing %s" % stat.name
        data = {
            'id': "#"+stat.name,
            'series': [
                {
                    "name": stat.name,
                    "data": stat.graph("hour", start=datetime.datetime.now())
                }
            ]
        }
        test['graphs'].append(data)
    return json.dumps(test, default=dthandler)


@sockets.route('/socket')
def socket(ws):
    while True:
        data = get_stats()
        ws.send(data)
        time.sleep(30)

@app.route('/')
def hello():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)


