"""
merge_duplicates.py
Safe, interactive helper to find duplicate emails in `customerdetails` and optionally merge them.
Usage:
  python scripts\merge_duplicates.py --dry-run
  python scripts\merge_duplicates.py --apply

It reads DB connection info from environment variables (same as your app):
  DB_HOST, DB_USERNAME, DB_PASSWORD, DB_DBNAME

By default it picks keep_id = MIN(user_id) for each email. It shows SQL statements it would run in dry-run.
If --apply is passed it executes the migration inside a transaction.

Make a backup before running --apply. Test on a copy first.
"""
import os
import mysql.connector
import argparse


def get_conn():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST'),
        user=os.environ.get('DB_USERNAME'),
        password=os.environ.get('DB_PASSWORD'),
        database=os.environ.get('DB_DBNAME'),
    )


def find_duplicates(conn):
    cur = conn.cursor()
    cur.execute("SELECT email, COUNT(*) as cnt FROM customerdetails GROUP BY email HAVING cnt > 1")
    rows = cur.fetchall()
    cur.close()
    return [r[0] for r in rows]


def get_ids_for_email(conn, email):
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM customerdetails WHERE email=%s ORDER BY user_id", (email,))
    rows = [r[0] for r in cur.fetchall()]
    cur.close()
    return rows


def merge_email(conn, email, keep_id, dup_ids, apply=False):
    cur = conn.cursor()
    stmts = []
    for dup in dup_ids:
        if dup == keep_id:
            continue
        stmts.append(("UPDATE cart SET user_id = %s WHERE user_id = %s;", (keep_id, dup)))
        stmts.append(("UPDATE orders SET user_id = %s WHERE user_id = %s;", (keep_id, dup)))
        stmts.append(("UPDATE address SET user_id = %s WHERE user_id = %s;", (keep_id, dup)))
        stmts.append(("DELETE FROM customerdetails WHERE user_id = %s;", (dup,)))

    if not apply:
        print(f"Dry-run for email={email}, keep_id={keep_id}, dup_ids={dup_ids}")
        for sql, params in stmts:
            print(cur.mogrify(sql, params) if hasattr(cur, 'mogrify') else (sql % params))
        return

    # Apply within a transaction
    try:
        for sql, params in stmts:
            cur.execute(sql, params)
        conn.commit()
        print(f"Applied merge for email={email}, keep_id={keep_id}")
    except Exception as e:
        conn.rollback()
        print(f"Failed merging {email}: {e}")
    finally:
        cur.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='Apply the migration')
    args = parser.parse_args()

    conn = get_conn()
    try:
        dups = find_duplicates(conn)
        if not dups:
            print('No duplicate emails found.')
            return

        for email in dups:
            ids = get_ids_for_email(conn, email)
            keep = min(ids)
            dup_ids = ids
            if args.apply:
                print(f"Applying merge for {email}: keep {keep}, remove {dup_ids}")
                merge_email(conn, email, keep, dup_ids, apply=True)
            else:
                print(f"Found duplicate email: {email} -> ids={ids}. Dry-run only.")
                merge_email(conn, email, keep, dup_ids, apply=False)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
