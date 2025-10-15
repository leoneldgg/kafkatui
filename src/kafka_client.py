from __future__ import annotations
from typing import List, Tuple
from kafka import KafkaAdminClient, KafkaConsumer, TopicPartition

class KafkaClient:
    def __init__(self, bootstrap_servers: str,  **kafka_kwargs):
        self.bootstrap_servers = bootstrap_servers
        self.kafka_kwargs = kafka_kwargs or {}
        self.admin = KafkaAdminClient(
            bootstrap_servers=bootstrap_servers, 
            client_id="kafkatui"
            , **self.kafka_kwargs
        )

    def list_topics(self) -> List[str]:
        return sorted(self.admin.list_topics())

    def partitions_for_topic(self, topic: str) -> List[int]:
        cons = KafkaConsumer(bootstrap_servers=self.bootstrap_servers, client_id="kafkatui-info", group_id=None)
        parts = cons.partitions_for_topic(topic) or set()
        cons.close()
        return sorted(parts)

    def topic_offsets(self, topic: str) -> Tuple[dict, dict]:
        cons = KafkaConsumer(bootstrap_servers=self.bootstrap_servers, client_id="kafkatui-offs", group_id=None)
        partitions = [TopicPartition(topic, p) for p in (cons.partitions_for_topic(topic) or [])]
        if not partitions:
            cons.close()
            return {}, {}
        earliest = cons.beginning_offsets(partitions)
        latest = cons.end_offsets(partitions)
        cons.close()
        return earliest, latest

    def topic_message_count(self, topic: str) -> int:
        earliest, latest = self.topic_offsets(topic)
        return sum(max(latest.get(tp, 0) - earliest.get(tp, 0), 0) for tp in latest.keys())

    def read_tail(self, topic: str, max_messages: int = 50):
        """Return up to `max_messages` most recent messages across all partitions."""
        cons = KafkaConsumer(
            bootstrap_servers=self.bootstrap_servers,
            client_id="kafkatui-tail",
            group_id=None,
            enable_auto_commit=False,
            auto_offset_reset="latest",
            consumer_timeout_ms=1500,
        )
        parts = cons.partitions_for_topic(topic) or set()
        partitions = [TopicPartition(topic, p) for p in parts]
        if not partitions:
            cons.close()
            return []
        cons.assign(partitions)
        beginnings = cons.beginning_offsets(partitions)
        ends = cons.end_offsets(partitions)
        for tp in partitions:
            start = max(ends[tp] - max_messages, beginnings[tp])
            cons.seek(tp, start)

        msgs = []
        for msg in cons:
            key = (msg.key.decode("utf-8", "replace") if isinstance(msg.key, (bytes, bytearray)) else (msg.key or ""))
            val = (msg.value.decode("utf-8", "replace") if isinstance(msg.value, (bytes, bytearray)) else (msg.value or ""))
            msgs.append((msg.partition, msg.offset, msg.timestamp, str(key), str(val)))
            if len(msgs) >= max_messages * 2:
                break
        cons.close()

        msgs.sort(key=lambda m: (m[2], m[1]), reverse=True)
        return msgs[:max_messages]
