# pages/1_講義室_座席予約.py
# 最大3人まで同時に席を選べる講義室座席予約ページ
# データベースは使用しません。予約情報はStreamlitを終了すると消えます。

from __future__ import annotations

from datetime import date
import math
import uuid

import streamlit as st

from db import get_connection
from i18n import apply_font_size, is_english, t


st.set_page_config(
    page_title=t("講義室の席予約", "Seat Reservation"),
    page_icon="💺",
    layout="wide",
)
apply_font_size()

# 講義室名: (座席の合計数, 横1行に並べる席数)
ROOMS = {
    "3101": (120, 12),
    "3102": (63, 9),
    "3103": (63, 9),
    "3104": (63, 9),
    "3201": (63, 9),
    "3202": (63, 9),
    "3203": (63, 9),
    "3204": (63, 9),
}

PERIODS = {
    "1限": "08:50～10:30",
    "2限": "10:40～12:20",
    "3限": "13:10～14:50",
    "4限": "15:00～16:40",
    "5限": "16:50～18:30",
}


def create_seat_names(capacity: int, seats_per_row: int) -> list[list[str]]:
    """定員に応じて A1, A2, B1... の座席名を作る。"""
    row_count = math.ceil(capacity / seats_per_row)
    seat_rows: list[list[str]] = []
    created = 0

    for row_index in range(row_count):
        row_name = chr(ord("A") + row_index)
        row: list[str] = []

        for column_index in range(1, seats_per_row + 1):
            if created >= capacity:
                break

            row.append(f"{row_name}{column_index}")
            created += 1

        seat_rows.append(row)

    return seat_rows


def reservation_key(
    room_name: str,
    reservation_date: date,
    period_name: str,
    seat_name: str,
) -> str:
    """同じ講義室・日付・時限・席の重複予約を判定するキー。"""
    return (
        f"{room_name}|{reservation_date.isoformat()}|"
        f"{period_name}|{seat_name}"
    )


def seat_sort_key(seat_name: str) -> tuple[str, int]:
    """A1、A2、A10の順に並べるためのキー。"""
    row_name = "".join(c for c in seat_name if c.isalpha())
    column_text = "".join(c for c in seat_name if c.isdigit())
    return row_name, int(column_text)


def period_time_to_db_values(period_name: str) -> tuple[str, str]:
    """時限表示を DB 保存用の時刻文字列へ変換する。"""
    start_time, end_time = PERIODS[period_name].split("～")
    return f"{start_time}:00", f"{end_time}:00"


def build_db_purpose(
    purpose_text: str,
    seats: list[str],
    number_of_people: int,
) -> str:
    """一覧で席情報も追えるよう、利用目的に補足情報を付ける。"""
    seat_text = ",".join(sorted(seats, key=seat_sort_key))
    return f"{purpose_text} / 席:{seat_text} / 人数:{number_of_people}"


def save_reservation_to_db(
    room_name: str,
    reservation_date: date,
    period_name: str,
    seats: list[str],
    number_of_people: int,
    reserver_name: str,
    student_number: str,
    purpose_text: str,
) -> None:
    """予約内容を reservations / reservation_periods に保存する。"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO students (student_no, name, pin)
            VALUES (%s, %s, '0000')
            ON DUPLICATE KEY UPDATE name = VALUES(name)
            """,
            (student_number, reserver_name),
        )

        cursor.execute(
            "SELECT room_id FROM rooms WHERE room_name = %s",
            (room_name,),
        )
        room_row = cursor.fetchone()

        if room_row:
            room_id = room_row[0]
        else:
            capacity, _ = ROOMS[room_name]
            cursor.execute(
                """
                INSERT INTO rooms (room_name, building, floor, capacity)
                VALUES (%s, %s, %s, %s)
                """,
                (room_name, "未設定", None, capacity),
            )
            room_id = cursor.lastrowid

        cursor.execute(
            "SELECT period_id FROM periods WHERE period_name = %s",
            (period_name,),
        )
        period_row = cursor.fetchone()

        if period_row:
            period_id = period_row[0]
        else:
            start_time, end_time = period_time_to_db_values(period_name)
            cursor.execute(
                """
                INSERT INTO periods (period_name, start_time, end_time)
                VALUES (%s, %s, %s)
                """,
                (period_name, start_time, end_time),
            )
            period_id = cursor.lastrowid

        cursor.execute(
            """
            SELECT status_id
            FROM reservation_statuses
            WHERE status_name = %s
            """,
            ("予約済",),
        )
        status_row = cursor.fetchone()

        if status_row:
            status_id = status_row[0]
        else:
            cursor.execute(
                """
                INSERT INTO reservation_statuses (status_name)
                VALUES (%s)
                """,
                ("予約済",),
            )
            status_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO reservations (
                room_id,
                reserved_date,
                student_no,
                reserver_name,
                status_id,
                purpose
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                room_id,
                reservation_date.isoformat(),
                student_number,
                reserver_name,
                status_id,
                build_db_purpose(
                    purpose_text,
                    seats,
                    number_of_people,
                ),
            ),
        )
        reservation_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO reservation_periods (reservation_id, period_id)
            VALUES (%s, %s)
            """,
            (reservation_id, period_id),
        )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


# -----------------------------
# セッション内の一時データ
# -----------------------------
if "seat_reservations" not in st.session_state:
    st.session_state.seat_reservations = {}

if "selected_seats" not in st.session_state:
    st.session_state.selected_seats = []

if "last_condition" not in st.session_state:
    st.session_state.last_condition = None

if "flash_message" not in st.session_state:
    st.session_state.flash_message = None


st.title(t("💺 講義室の席予約", "💺 Seat Reservation"))
st.caption(t("1人から最大3人まで、人数分の空席を選択して一度に予約できます。", "You can reserve seats for 1 to 3 people at once."))

st.warning(
    t(
        "このページは画面だけで動作します。予約情報はブラウザを開いている間だけ保存され、"
        "Streamlitを終了すると消えます。",
        "This page uses on-screen temporary state. Session-based seat status is cleared when Streamlit stops.",
    )
)

if st.session_state.flash_message:
    st.success(st.session_state.flash_message)
    st.session_state.flash_message = None


# -----------------------------
# 1. 予約条件
# -----------------------------
st.subheader(t("1. 講義室・日付・時限・人数を選択", "1. Choose Room, Date, Period, and People"))

col1, col2, col3, col4 = st.columns(4)

with col1:
    selected_room = st.selectbox(t("講義室", "Room"), list(ROOMS.keys()))

with col2:
    selected_date = st.date_input(
        t("予約日", "Reservation Date"),
        value=date.today(),
        min_value=date.today(),
    )

with col3:
    selected_period = st.selectbox(
        t("時限", "Period"),
        list(PERIODS.keys()),
        format_func=lambda name: f"{name}（{PERIODS[name]}）",
    )

with col4:
    number_of_people = st.selectbox(
        t("予約人数", "Number of People"),
        options=[1, 2, 3],
        format_func=(lambda number: f"{number} people") if is_english() else (lambda number: f"{number}人"),
    )

current_condition = (
    selected_room,
    selected_date.isoformat(),
    selected_period,
    number_of_people,
)

# 条件が変わったら選択中の席を解除
if st.session_state.last_condition != current_condition:
    st.session_state.selected_seats = []
    st.session_state.last_condition = current_condition


# -----------------------------
# 2. 座席表
# -----------------------------
capacity, seats_per_row = ROOMS[selected_room]
seat_rows = create_seat_names(capacity, seats_per_row)

if is_english():
    st.subheader(f"2. Select {number_of_people} available seat(s)")
else:
    st.subheader(f"2. 空いている席を{number_of_people}席選択")

st.markdown(
    f"""
    <div style="
        text-align:center;
        border:2px solid #888;
        border-radius:8px;
        padding:10px;
        margin:8px 0 20px 0;
        font-weight:bold;
    ">
        {t("教卓・スクリーン", "Teacher Desk / Screen")}
    </div>
    """,
    unsafe_allow_html=True,
)

legend1, legend2, legend3 = st.columns(3)
legend1.success(t("🟩 空席", "🟩 Available"))
legend2.warning(t("🟨 選択中", "🟨 Selected"))
legend3.error(t("🟥 予約済み", "🟥 Reserved"))

selected_count = len(st.session_state.selected_seats)
st.progress(
    selected_count / number_of_people,
    text=(
        f"Selected: {selected_count} / {number_of_people}"
        if is_english()
        else f"選択済み：{selected_count} / {number_of_people}席"
    ),
)

for row in seat_rows:
    columns = st.columns(len(row))

    for column, seat_name in zip(columns, row):
        key = reservation_key(
            selected_room,
            selected_date,
            selected_period,
            seat_name,
        )

        is_reserved = key in st.session_state.seat_reservations
        is_selected = seat_name in st.session_state.selected_seats

        if is_reserved:
            label = f"🟥 {seat_name}"
        elif is_selected:
            label = f"🟨 {seat_name}"
        else:
            label = f"🟩 {seat_name}"

        with column:
            if st.button(
                label,
                key=f"seat_button_{key}",
                disabled=is_reserved,
                use_container_width=True,
            ):
                if is_selected:
                    st.session_state.selected_seats.remove(seat_name)
                elif len(st.session_state.selected_seats) < number_of_people:
                    st.session_state.selected_seats.append(seat_name)
                else:
                    st.toast(
                        (
                            f"You can select up to {number_of_people} seat(s)."
                            if is_english()
                            else f"選択できるのは{number_of_people}席までです。"
                        ),
                        icon="⚠️",
                    )

                st.rerun()

selected_seats = sorted(
    st.session_state.selected_seats,
    key=seat_sort_key,
)

seat_info_col, clear_col = st.columns([4, 1])

with seat_info_col:
    if selected_seats:
        st.info(t("選択中の席：", "Selected seats: ") + "、".join(selected_seats))
    else:
        st.info(t("まだ席を選択していません。", "No seats selected yet."))

with clear_col:
    if st.button(
        t("選択を解除", "Clear selection"),
        disabled=not selected_seats,
        use_container_width=True,
    ):
        st.session_state.selected_seats = []
        st.rerun()


# -----------------------------
# 3. 代表者情報
# -----------------------------
st.subheader(t("3. 代表者情報を入力", "3. Enter Representative Info"))

form_col1, form_col2 = st.columns(2)

with form_col1:
    reserver_name = st.text_input(
        t("代表者氏名", "Representative Name"),
        placeholder=t("例：山田 太郎", "Example: Taro Yamada"),
    )

    student_number = st.text_input(
        t("代表者の学籍番号", "Representative Student Number"),
        placeholder=t("例：A1234567", "Example: A1234567"),
    )

with form_col2:
    purpose = st.text_area(
        t("利用目的", "Purpose"),
        placeholder=t("例：講義の受講、ゼミ、勉強会", "Example: Lecture, seminar, study group"),
        height=110,
    )


# -----------------------------
# 4. 予約確認
# -----------------------------
st.subheader(t("4. 予約内容を確認", "4. Confirm Reservation"))

st.write(f"**{t('講義室', 'Room')}：** {selected_room}")
if is_english():
    st.write(f"**{t('予約日', 'Reservation Date')}：** {selected_date.strftime('%Y-%m-%d')}")
else:
    st.write(f"**{t('予約日', 'Reservation Date')}：** {selected_date.strftime('%Y年%m月%d日')}")
st.write(f"**{t('時限', 'Period')}：** {selected_period}（{PERIODS[selected_period]}）")
if is_english():
    st.write(f"**{t('人数', 'People')}：** {number_of_people}")
else:
    st.write(f"**{t('人数', 'People')}：** {number_of_people}人")
st.write(
    f"**{t('座席', 'Seats')}：** "
    + ("、".join(selected_seats) if selected_seats else t("未選択", "Not selected"))
)

correct_seat_count = len(selected_seats) == number_of_people
required_fields_entered = all(
    [
        reserver_name.strip(),
        student_number.strip(),
        purpose.strip(),
    ]
)
can_reserve = correct_seat_count and required_fields_entered

if not correct_seat_count:
    if is_english():
        st.info(f"Please select {number_of_people} seat(s).")
    else:
        st.info(f"{number_of_people}人分の席を選択してください。")

if not required_fields_entered:
    st.info(t("代表者氏名・学籍番号・利用目的をすべて入力してください。", "Please fill in name, student number, and purpose."))

if st.button(
    (
        f"Reserve for {number_of_people} person(s)"
        if is_english()
        else f"{number_of_people}人分を予約する"
    ),
    type="primary",
    disabled=not can_reserve,
    use_container_width=True,
):
    seat_keys = [
        reservation_key(
            selected_room,
            selected_date,
            selected_period,
            seat_name,
        )
        for seat_name in selected_seats
    ]

    duplicate_seats = [
        seat_name
        for key, seat_name in zip(seat_keys, selected_seats)
        if key in st.session_state.seat_reservations
    ]

    if duplicate_seats:
        st.error(
            t("次の席はすでに予約されています：", "These seats are already reserved: ")
            + "、".join(duplicate_seats)
        )
    else:
        try:
            save_reservation_to_db(
                room_name=selected_room,
                reservation_date=selected_date,
                period_name=selected_period,
                seats=selected_seats,
                number_of_people=number_of_people,
                reserver_name=reserver_name.strip(),
                student_number=student_number.strip(),
                purpose_text=purpose.strip(),
            )
        except Exception as error:
            if is_english():
                st.error(f"Failed to save to DB: {error}")
            else:
                st.error(f"DBへの保存に失敗しました: {error}")
        else:
            group_id = str(uuid.uuid4())

            for key, seat_name in zip(seat_keys, selected_seats):
                st.session_state.seat_reservations[key] = {
                    "group_id": group_id,
                    "room": selected_room,
                    "date": selected_date.isoformat(),
                    "period": selected_period,
                    "period_time": PERIODS[selected_period],
                    "seat": seat_name,
                    "number_of_people": number_of_people,
                    "reserver_name": reserver_name.strip(),
                    "student_number": student_number.strip(),
                    "purpose": purpose.strip(),
                }

            reserved_seat_text = "、".join(selected_seats)
            st.session_state.selected_seats = []
            st.session_state.flash_message = (
                (
                    f"Reserved {reserved_seat_text} in room {selected_room}."
                    if is_english()
                    else f"{selected_room}教室の{reserved_seat_text}を予約しました。"
                )
            )
            st.rerun()

