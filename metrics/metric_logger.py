import time
import csv

class MetricLogger:
    def __init__(self, filename="metrics.csv"):
        self.filename = filename
        self.records = []

    def log(self, seq, sent_time, recv_time, retransmissions=0):
        latency = recv_time - sent_time
        self.records.append({
            "seq": seq,
            "latency": latency,
            "retransmissions": retransmissions
        })

    def save(self):
        keys = ["seq", "latency", "retransmissions"]
        with open(self.filename, "w", newline="") as f:
            writer = csv.DictWriter(f, keys)
            writer.writeheader()
            writer.writerows(self.records)
