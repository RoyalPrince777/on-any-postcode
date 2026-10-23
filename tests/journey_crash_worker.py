"""Test-only process killed around a real ephemeral PostgreSQL commit."""
import json
import os
import re
import signal
import sys
from contextlib import contextmanager
from urllib.parse import urlsplit

from psycopg import sql

from mission_control import oap_eats_fulfilment, oap_eats_store, postgres_db

assert os.getenv("OAP_REAL_POSTGRES_PROOF") == "1"
assert urlsplit(postgres_db._database_url()).hostname in {"127.0.0.1", "localhost", "::1"}
schema = os.environ["OAP_EATS_TEST_SCHEMA"]
assert re.fullmatch(r"oap_eats_test_[0-9a-f]{32}", schema)
payload = json.load(sys.stdin)
original = postgres_db.connect


class CrashConnection:
    def __init__(self, db):
        self.db = db

    def execute(self, *args):
        return self.db.execute(*args)

    def commit(self):
        if payload["phase"] == "after_commit":
            self.db.commit()
        print(payload["phase"], flush=True)
        signal.pause()
        raise AssertionError("worker_should_be_killed")


@contextmanager
def connect(*, readonly=False):
    with original(readonly=readonly) as db:
        db.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
        db.execute("SET LOCAL statement_timeout='10s'")
        yield CrashConnection(db)


postgres_db.connect = connect
if payload["action"] == "create":
    oap_eats_fulfilment.create_delivery(**payload["args"])
else:
    oap_eats_store.STORE.transition(**payload["args"])
