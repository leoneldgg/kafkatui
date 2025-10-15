# producer.py
import argparse, json, time, random, string
from kafka import KafkaProducer

def rand_str(n=8): return ''.join(random.choices(string.ascii_letters + string.digits, k=n))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bootstrap", default="127.0.0.1:9094")
    ap.add_argument("--topic", required=True)
    ap.add_argument("--messages", type=int, default=50)
    ap.add_argument("--rps", type=float, default=5.0, help="messages per second")
    ap.add_argument("--json", action="store_true", help="send JSON payloads")
    args = ap.parse_args()

    producer = KafkaProducer(
        bootstrap_servers=args.bootstrap,
        key_serializer=lambda k: k.encode() if k is not None else None,
        value_serializer=(lambda v: json.dumps(v).encode()) if args.json else (lambda v: v.encode()),
    )

    interval = 1.0 / max(args.rps, 0.001)
    for i in range(args.messages):
        key = rand_str(6)
        val = {"i": i, "msg": rand_str(16)} if args.json else f"msg#{i}:{rand_str(16)}"
        producer.send(args.topic, key=key, value=val)
        if (i + 1) % 100 == 0: producer.flush()
        time.sleep(interval)

    producer.flush()
    print(f"Sent {args.messages} messages to {args.topic}")

if __name__ == "__main__":
    main()
