def recalc_balances(conn, student_id: int) -> None:
    """按记账顺序重算指定学员全部余额记录的结余，保证流水结余连续。"""
    rows = conn.execute(
        'SELECT record_id, hours FROM balance_record WHERE student_id = ? '
        'ORDER BY record_date ASC, record_id ASC', (student_id,)
    ).fetchall()
    current = 0
    for record_id, hours in rows:
        current += hours
        conn.execute('UPDATE balance_record SET balance = ? WHERE record_id = ?', (current, record_id))
