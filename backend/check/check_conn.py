"""Connectivity check: MySQL + Redis, config loaded from backend/.env"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]


def load_env(path: Path) -> dict:
    env = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip()
    return env


def check_mysql(env: dict) -> None:
    import pymysql

    conn = pymysql.connect(
        host=env["MYSQL_HOST"],
        port=int(env["MYSQL_PORT"]),
        user=env["MYSQL_USER"],
        password=env["MYSQL_PASSWORD"],
        database=env["MYSQL_DATABASE"],
        connect_timeout=5,
    )
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT VERSION()")
            version = cur.fetchone()[0]
            cur.execute("SHOW TABLES")
            tables = [r[0] for r in cur.fetchall()]
        print(f"[OK] MySQL {version} @ {env['MYSQL_HOST']}:{env['MYSQL_PORT']}/{env['MYSQL_DATABASE']}")
        print(f"     existing tables: {tables if tables else '(empty, init.sql not executed yet)'}")
    finally:
        conn.close()


def check_redis(env: dict) -> None:
    import redis

    client = redis.Redis(
        host=env["REDIS_HOST"],
        port=int(env["REDIS_PORT"]),
        db=int(env.get("REDIS_DB") or 0),
        password=env.get("REDIS_PASSWORD") or None,
        socket_connect_timeout=5,
    )
    pong = client.ping()
    client.set("defect:conn-test", "ok", ex=30)
    value = client.get("defect:conn-test")
    client.delete("defect:conn-test")
    print(f"[OK] Redis PING={pong}, SET/GET test value={value.decode()}, test key cleaned up")


def main() -> int:
    env_path = BACKEND_DIR / ".env"
    if not env_path.exists():
        print(f"[FAIL] .env not found: {env_path}")
        return 1
    env = load_env(env_path)
    print(f"[INFO] config loaded from {env_path}")
    failures = []
    for name, fn in (("MySQL", check_mysql), ("Redis", check_redis)):
        try:
            fn(env)
        except Exception as exc:
            failures.append(name)
            print(f"[FAIL] {name}: {type(exc).__name__}: {exc}")
    if failures:
        print(f"[FAIL] connectivity check failed: {', '.join(failures)}")
        return 1
    print("[PASS] all connectivity checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
