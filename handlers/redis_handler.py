from handlers import Handler
from utils.grapher import Graph
import redis

class RedisHandler(Handler):
    def __init__(self):
        self.master.register_metric("redis_get_info", self.metric_get_info)

        self.graphs.addStat(Graph("redis_clients"))
        self.graphs.addStat(Graph("redis_memory"))

    def metric_get_info(self):
        client = self.master.get_redis()
        data = client.info()

        self.graphs.set("redis_clients", data['connected_clients'])
        self.graphs.set("redis_memory", data['used_memory'])
