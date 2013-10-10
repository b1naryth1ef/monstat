from handlers import Handler
from utils.grapher import Graph, MultiGraph
import pymongo

class MongoHandler(Handler):
    def __init__(self):
        self.master.register_metric("mongo_get_info", self.metric_get_info)

        self.stats = {}
        self.mstats = []

        for obj_name in self.config.get("objs", []):
            self.stats[obj_name] = {}
            for db in self.config.get("dbs", []):
                self.stats[obj_name][db] = self.graphs.addStat(Graph("mongodb_%s_%s" % (obj_name, db), formatter=float))
            self.mstats.append(self.graphs.addStat(MultiGraph("mongodb_%s" % obj_name, self.stats[obj_name])))

    def metric_get_info(self):
        client = pymongo.MongoClient(host=self.config.get("host"))

        for obj, values in self.stats.items():
            for k, v in values.items():
                data = client[k].command({"dbstats": 1})
                v.set(data[obj])
