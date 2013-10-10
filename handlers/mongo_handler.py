from handlers import Handler
from utils.grapher import Graph, MultiGraph
import pymongo

def super_key(keyset, value):
    for item in keyset.split("|"):
        value = value[item]
    return value

class MongoHandler(Handler):
    def __init__(self):
        self.master.register_metric("mongo_get_info", self.metric_get_info)

        self.stats = {}
        self.mstats = []

        self.mgraphs = {}

        for obj_name in self.config.get("objs", []):
            self.stats[obj_name] = {}
            for db in self.config.get("dbs", []):
                self.stats[obj_name][db] = self.graphs.addStat(Graph("mongodb_%s_%s" % (obj_name, db), formatter=float))
            self.mstats.append(self.graphs.addStat(MultiGraph("mongodb_%s" % obj_name, self.stats[obj_name])))

        self.mgraphs['conns'] = self.graphs.addStat(MultiGraph("mongodb_conns", [
            self.graphs.addStat(Graph("mongodb_connections", alias="connections|current")),
            ]))

        self.mgraphs['indexes'] = self.graphs.addStat(MultiGraph("mongodb_indexes", [
                Graph("mongodb_indexes_missRatio", alias="indexCounters|btree|missRatio"),
                Graph("mongodb_indexes_hits", alias="indexCounters|btree|hits"),
                Graph("mongodb_indexes_misses", alias="indexCounters|btree|misses"),
            ]))

        self.mgraphs['ops'] = self.graphs.addStat(MultiGraph("mongodb_opcounter", [
                Graph("mongodb_opcounter_insert", alias="opcounters|insert"),
                Graph("mongodb_opcounter_query", alias="opcounters|query"),
                Graph("mongodb_opcounter_update", alias="opcounters|update"),
                Graph("mongodb_opcounter_delete", alias="opcounters|delete"),
                Graph("mongodb_opcounter_command", alias="opcounters|command")
            ]))

    def metric_get_info(self):
        client = pymongo.MongoClient(host=self.config.get("host"))

        # DB specific graphs
        for obj, values in self.stats.items():
            for k, v in values.items():
                data = client[k].command({"dbstats": 1})
                v.set(data[obj])

        data = client[k].command({"serverStatus": 1})

        for graph in self.mgraphs.values():
            for subgraph in graph.graphs.values():
                subgraph.set(super_key(subgraph.alias, data))

        #self.mgraphs.graphs['mongodb_opcounter_insert'].
