import time, json
import os, sys, redis

from utils.grapher import GraphManager

class Master(object):
    def __init__(self):
        self.handlers = {}
        self.metrics = {}
        self.config = {}
        self.load_config()

        self.graphs = GraphManager(self.get_redis())

        for handler in self.config.get('handlers', []):
            try:
                name = handler.rsplit(".", 1)
                __import__(name[0])
                self.handlers[handler] = getattr(sys.modules[name[0]], name[-1])
                self.handlers[handler].master = self
                self.handlers[handler].graphs = self.graphs
                self.handlers[handler].config = self.config.get(name[-1], {})
                self.handlers[handler] = self.handlers[handler]()
                print "Loaded handler %s" % handler
            except ImportError, e:
                print e

    def alert(self, namespace, text, t="warning"):
        self.get_redis().lpush("alert."+namespace, json.dumps({
            "text": text,
            "type": t,
            "space": namespace
        }))

    def rmv_alerts(self, namespace):
        for k in self.get_redis().keys("alert."+namespace+"*"):
            self.get_redis().delete(k)

    def get_alerts(self, namespace=None):
        key = "alert."+(namespace if namespace else "")+"*"
        results = []
        for k in self.get_redis().keys(key):
            for value in self.get_reds().lrange(k, 0, -1):
                results.append(json.loads(value))
        return results

    def get_redis(self):
        red = self.config.get("redis")
        if not red:
            raise Exception("Key `redis` not in config, breaking!")
        return redis.Redis(host=red.get("host"), password=red.get("pw"))

    def load_config(self):
        if not os.path.exists("config.json"):
            raise Exception("Config does not exist!")
        with open("config.json", "r") as f:
            self.config = json.load(f)

    def save_config(self):
        with open("config.json", "w") as f:
            json.dump(f, self.config)

    def update(self):
        for metric in self.metrics.values():
            metric()

    def register_metric(self, name, call_back):
        self.metrics[name] = call_back

    def loop(self):
        while True:
            time.sleep(self.config.get("resolution_time", 30))
            self.update()

if __name__ == "__main__":
    m = Master()
    m.loop()
