from handlers import Handler
from utils.grapher import Graph, MultiGraph
import paramiko

class Conn(object):
    def __init__(self, host, user):
        self.host = host
        self.user = user
        self.conn = None

    def __enter__(self):
        self.conn = paramiko.SSHClient()
        self.conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.conn.connect(self.host, username=self.user)

    def __exit__(self, *args, **kwargs):
        self.conn.close()

class SysStat(object):
    name = "load"
    cmd = "echo 0"

    @classmethod
    def run(cls, c):
        self = cls()
        with c:
            a, b, c = c.conn.exec_command(self.cmd)
            return self.parse(a, b, c)

    def parse(self, stdin, stdout, stderr):
        return True


class StatLoad(SysStat):
    name = "load"
    cmd = "uptime | awk -F'[a-z]:' '{ print $2}'"

    def parse(self, stdin, stdout, stderr):
        a, b, c = stdout.read().split(", ")
        return {
            "1": a,
            "5": b,
            "15": c
        }

split_spaces = lambda a: [i for i in a.split(" ") if i != ""]

class StatMemory(SysStat):
    name = "memory"
    cmd = "free"

    def parse(self, stdin, stdout, stderr):
        vals = split_spaces(stdout.read().split("\n")[1])
        return {
            "total": vals[1],
            "used": vals[2],
            "free": vals[3],
            "shared": vals[4],
            "buffers": vals[5],
            "cached": vals[6]
        }

class StatDisk(SysStat):
    name = "disk"
    cmd = "free"

    def parse(self, stdin, stdout, stderr):
        results = {}
        for line in stdout.read().split("\n")[1:]:
            if line.startswith("/dev/"):
                data = split_spaces(line)
                results[data[0]+" use"] = data[4]
        return results

SYS_STATS = {
    "load": StatLoad,
    "memory": StatMemory,
    "disk": StatDisk
}

class SysHandler(Handler):
    def __init__(self):
        self.master.register_metric("sys_update", self.metric_sys_update)
        self.hosts = {}
        self.gz = {}

        for host in self.config.get("hosts"):
            self.hosts[host['host']] = Conn(host['host'], host['user'])
            self.gz[host['host']] = []
            for graph in self.config.get("metrics"):
                self.gz[host['host']].append([graph, self.graphs.addStat(MultiGraph("%s_%s" % (host['host'], graph), []))])

    def metric_sys_update(self, notset=True):
        for k, v in self.hosts.items():
            for a, b in self.gz[k]:
                for y, z in SYS_STATS[a].run(v).items():
                    name = b.name+"_"+y
                    if name not in b.graphs.keys():
                        b.add(Graph(name))
                    if not notset: b.graphs[name].set(z, True)
        # client = self.master.get_redis()
        # data = client.info()

        # self.graphs.set("redis_clients", data['connected_clients'])
        # self.graphs.set("redis_memory", data['used_memory'])
