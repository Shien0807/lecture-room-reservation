from __future__ import annotations

from datetime import date

import streamlit as st

from db import get_connection
from i18n import apply_font_size, is_english, t


def fetch_room_names() -> list[str]:
    """講義室名の候補を DB から取得する。"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT room_name FROM rooms ORDER BY room_name")
        return [row[0] for row in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()


def fetch_reservations(
    room_name: str | None,
    reserved_date: date | None,
    period_name: str | None,
) -> list[tuple]:
    """条件付きで予約一覧を取得する。"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        sql = """
            SELECT
                r.reservation_id,
                rm.room_name,
                r.reserved_date,
                GROUP_CONCAT(p.period_name ORDER BY p.period_id SEPARATOR ',') AS periods,
                r.reserver_name,
                r.student_no,
                rs.status_name,
                COALESCE(r.purpose, ''),
                r.created_at
            FROM reservations r
            JOIN rooms rm
                ON rm.room_id = r.room_id
            JOIN reservation_statuses rs
                ON rs.status_id = r.status_id
            LEFT JOIN reservation_periods rp
                ON rp.reservation_id = r.reservation_id
            LEFT JOIN periods p
                ON p.period_id = rp.period_id
            WHERE 1 = 1
        """
        params: list = []

        if room_name:
            sql += " AND rm.room_name = %s"
            params.append(room_name)

        if reserved_date:
            sql += " AND r.reserved_date = %s"
            params.append(reserved_date.isoformat())

        if period_name:
            sql += " AND p.period_name = %s"
            params.append(period_name)

        sql += """
            GROUP BY
                r.reservation_id,
                rm.room_name,
                r.reserved_date,
                r.reserver_name,
                r.student_no,
                rs.status_name,
                r.purpose,
                r.created_at
            ORDER BY r.reserved_date DESC, r.created_at DESC
        """

        cursor.execute(sql, tuple(params))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


st.set_page_config(page_title=t("予約一覧", "Reservation List"), page_icon="📋", layout="wide")
apply_font_size()

st.title(t("📋 予約一覧", "📋 Reservation List"))
st.caption(t("1_講義室_座席予約.py から保存された予約データを表示します。", "Shows reservations saved from 1_講義室_座席予約.py."))

rooms = fetch_room_names()

filter_col1, filter_col2, filter_col3 = st.columns(3)

with filter_col1:
    selected_room = st.selectbox(
        t("講義室", "Room"),
        options=[t("すべて", "All")] + rooms,
        index=0,
    )

with filter_col2:
    use_date_filter = st.checkbox(t("予約日で絞り込み", "Filter by Date"))
    selected_date = st.date_input(t("予約日", "Reservation Date"), value=date.today(), disabled=not use_date_filter)

with filter_col3:
    selected_period = st.selectbox(
        t("時限", "Period"),
        options=[t("すべて", "All"), "1限", "2限", "3限", "4限", "5限"],
        index=0,
    )

all_label = t("すべて", "All")
room_filter = None if selected_room == all_label else selected_room
period_filter = None if selected_period == all_label else selected_period
date_filter = selected_date if use_date_filter else None

rows = fetch_reservations(
    room_name=room_filter,
    reserved_date=date_filter,
    period_name=period_filter,
)

if not rows:
    st.info(t("該当する予約データはありません。", "No reservation data matched."))
else:
    if is_english():
        st.success(f"Found {len(rows)} reservations.")
    else:
        st.success(f"{len(rows)}件の予約が見つかりました。")

    table_rows = [
        {
            t("予約ID", "Reservation ID"): row[0],
            t("講義室", "Room"): row[1],
            t("予約日", "Reserved Date"): row[2],
            t("時限", "Period"): row[3] or t("未設定", "Not set"),
            t("予約者", "Reserver"): row[4],
            t("学籍番号", "Student Number"): row[5],
            t("状態", "Status"): row[6],
            t("利用目的", "Purpose"): row[7],
            t("作成日時", "Created At"): row[8],
        }
        for row in rows
    ]
    st.dataframe(table_rows, use_container_width=True, hide_index=True)
