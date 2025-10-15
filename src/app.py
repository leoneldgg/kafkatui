from ui.main import KafkaTUI
import argparse

def build_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bootstrap", default="127.0.0.1:9094", help="Bootstrap servers host:port")
    # Seguridad opcional
    ap.add_argument("--security-protocol", default="PLAINTEXT",
                    choices=["PLAINTEXT", "SASL_PLAINTEXT", "SASL_SSL", "SSL"])
    ap.add_argument("--sasl-mechanism", choices=["PLAIN", "SCRAM-SHA-256", "SCRAM-SHA-512",
                                                 "OAUTHBEARER", "GSSAPI"])
    ap.add_argument("--username")
    ap.add_argument("--password")
    # SSL (opcional)
    ap.add_argument("--ssl-cafile")
    ap.add_argument("--ssl-certfile")
    ap.add_argument("--ssl-keyfile")
    return ap.parse_args()


if __name__ == "__main__":
    args = build_args()

    kafka_kwargs = {
        "security_protocol": args.security_protocol,
    }

    if args.sasl_mechanism:
        kafka_kwargs["sasl_mechanism"] = args.sasl_mechanism
    if args.username is not None:
        kafka_kwargs["sasl_plain_username"] = args.username
    if args.password is not None:
        kafka_kwargs["sasl_plain_password"] = args.password
    if args.ssl_cafile:
        kafka_kwargs["ssl_cafile"] = args.ssl_cafile
    if args.ssl_certfile:
        kafka_kwargs["ssl_certfile"] = args.ssl_certfile
    if args.ssl_keyfile:
        kafka_kwargs["ssl_keyfile"] = args.ssl_keyfile

    app = KafkaTUI(bootstrap_servers=args.bootstrap, kafka_kwargs=kafka_kwargs)

    app.run()