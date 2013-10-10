import schedule, time, json
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

        schedule.every(self.config.get("resolution_time", 60)).seconds.do(self.update)

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

    def loop(self):
        while True:
            time.sleep(1)
            schedule.run_pending()

    def register_metric(self, name, call_back):
        self.metrics[name] = call_back

if __name__ == "__main__":
    m = Master()
    m.loop()
