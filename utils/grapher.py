from datetime import datetime, timedelta
from dateutil.rrule import *

#stat.name.YEAR.DAY.HOUR.MINUTE
base_key = "{key}.{d.year}.{d.day}.{d.hour}.{d.minute}"

# Averages a list
average = lambda l: reduce(lambda x, y: x + y, l) / float(len(l))

def get_keys(key, dt):
    """
    Returns a list of recursive date formated keys based on base_key.
    """
    res = []
    key = base_key.format(key=key, d=dt).split(".")
    for i in range(0, len(key)):
        res.append('.'.join(key[:i+1]))
    return res

class GraphManager(object):
    """
    Manages a collection of graphs for easy access
    """
    def __init__(self, redis):
        self.redis = redis
        self.stats = []

        for k in ["incr", "get", "set", "graph", "clear", "set_at", "incr_at", "boolean", "boolean_at", "variation", "average"]:
            self.__dict__[k] = self.smart_get(k)

    def addStat(self, stat):
        self.stats.append(stat)
        stat.init(self)
        return stat

    def rmvStat(self, stat):
        self.stats.remove(stat)

    def getStat(self, name):
        for s in self.stats:
            if s.name == name:
                return s

    def smart_get(self, funcname):
        def get(name, *args, **kwargs):
            return getattr(self.getStat(name), funcname)(*args, **kwargs)
        return get

class MultiGraph(object):
    """
    Combines multiple graphs for use in a series graph
    """
    def __init__(self, name, graphs):
        self.name = name
        self.graphs = {i.name: i for i in graphs.values()}

        for k in ["incr", "get", "set", "graph", "clear", "set_at", "incr_at", "boolean", "boolean_at", "variation", "average"]:
            self.__dict__[k] = self.smart_get(k)

    def init(self, manager):
        for i in self.graphs.values():
            i.parent = False
            i.init(manager)

    def smart_get(self, funcname):
        def get(*args, **kwargs):
            result = {}
            for n, g in self.graphs.items():
                result[n] = getattr(g, funcname)(*args, **kwargs)
            return result
        return get

class Graph(object):
    """
    A graph support setting, incrementing, and eventually getting
    data in the form of a time-series graph
    """
    def __init__(self, name, archive_time=30, formatter=int, boolean=False):
        self.name = name
        self.archive = archive_time
        self._formatter = formatter
        self.isboolean = boolean

        self.key = "stat.%s" % self.name
        self.red = None
        self.manager = None
        self.parent = True

    # hack
    def formatter(self, i):
        if i:
            return self._formatter(i)

    def init(self, manager):
        self.manager = None
        self.red = manager.redis

    def incr(self, val):
        self.incr_at(datetime.now(), val)

    def set(self, val, verbose=False):
        if verbose: print "Setting %s to %s at %s" % (self.name, val, datetime.now())
        self.set_at(datetime.now(), val)

    def graph_util(self, graph_type, start=None):
        by, kid, count = None, 0, 0
        if graph_type == "halfhour":
            by = MINUTELY
            kid = -1
            count = 30
            start = start+timedelta(minutes=-29)
        elif graph_type == "hour":
            by = MINUTELY
            kid = -1
            count = 60
            start = start+timedelta(minutes=-59)
        elif graph_type == "day":
            by = HOURLY
            kid = -2
            count = 24
            start = start+timedelta(hours=-23)
        elif graph_type == "week":
            by = DAILY
            kid = -3
            count = 7
            start = start+timedelta(days=-6)
        elif graph_type == "month":
            by = DAILY
            kid = -3
            count = 30
            start = start+timedelta(days=-29)
        return by, kid, count, start

    def average(self, graph_type, start=None):
        by, kid, count, start = self.graph_util(graph_type, start)
        result = []
        for dt in rrule(by, count=count, dtstart=start):
            k = get_keys(self.key, dt)[kid]
            allz = []
            for subkey in self.red.keys(k+"*"):
                allz.append(self.formatter(self.red.get(subkey) or 0))
            if len(allz):
                result.append([dt, average(allz)])
            else:
                result.append([dt, 0])
        return result

    def variation(self, graph_type, start=None):
        by, kid, count, start = self.graph_util(graph_type, start)
        result = []
        for dt in rrule(by, count=count, dtstart=start):
            k = get_keys(self.key, dt)[kid]
            allz = []
            for subkey in self.red.keys(k+"*"):
                allz.append(self.formatter(self.red.get(subkey) or 0))
            if not len(allz):
                result.append([dt, (0, 0)])
            else:
                result.append([dt, (min(allz), max(allz))])
        return result

    def graph(self, graph_type, start=None):
        by, kid, count, start = self.graph_util(graph_type, start)
        result = []
        for dt in rrule(by, count=count, dtstart=start):
            k = get_keys(self.key, dt)[kid]
            result.append([dt, self.formatter(self.red.get(k))])

        return result

    def clear(self):
        for k in self.red.keys(self.key+"*"):
            self.red.delete(k)

    def set_at(self, dt, val):
        for k in get_keys(self.key, dt):
            self.red.set(k, val)

    def incr_at(self, dt, val):
        for k in get_keys(self.key, dt):
            self.red.incr(k, val)

    def get_at(self, dt):
        k = get_keys(self.key, dt)[-1]
        return self.formatter(self.red.get(k) or 0)

    def boolean_at(self, dt):
        for k in get_keys(self.key, dt):
            self.red.set(k, 1)

    def boolean(self):
        self.boolean_at(datetime.now())
