import streamlit as st

from i18n import apply_font_size

st.set_page_config(page_title="ホーム画面", page_icon="🏠", layout="wide")

if "account_name" not in st.session_state:
    st.session_state.account_name = ""
if "account_student_no" not in st.session_state:
    st.session_state.account_student_no = ""
if "font_size" not in st.session_state:
    st.session_state.font_size = "普通"
if "language" not in st.session_state:
    st.session_state.language = "日本語"

language = st.session_state.language

apply_font_size()

if language == "日本語":
    page_title = "🏠 ホーム画面"
    page_caption = "予約機能への移動と、表示設定をここで管理します。"
    reservation_section = "登録（予約）"
    reservation_button = "登録（予約）を開く"
    settings_section = "設定"
    account_section = "アカウント情報"
    name_label = "氏名"
    student_no_label = "学籍番号"
    font_label = "文字の大きさ"
    language_label = "言語"
    save_button = "設定を保存"
    saved_message = "設定を保存しました。"
    current_section = "現在の設定"
    account_name_label = "氏名"
    account_student_no_label = "学籍番号"
else:
    page_title = "🏠 Home"
    page_caption = "Manage navigation and display settings here."
    reservation_section = "Reservation"
    reservation_button = "Open Reservation"
    settings_section = "Settings"
    account_section = "Account"
    name_label = "Name"
    student_no_label = "Student Number"
    font_label = "Font Size"
    language_label = "Language"
    save_button = "Save Settings"
    saved_message = "Settings saved."
    current_section = "Current Settings"
    account_name_label = "Name"
    account_student_no_label = "Student Number"

st.title(page_title)
st.caption(page_caption)

st.subheader(reservation_section)
if st.button(reservation_button):
    st.switch_page("pages/1_講義室_座席予約.py")

st.subheader(settings_section)

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"**{account_section}**")
    account_name = st.text_input(name_label, value=st.session_state.account_name)
    account_student_no = st.text_input(student_no_label, value=st.session_state.account_student_no)

with col2:
    selected_font = st.selectbox(font_label, ["普通", "大きい"], index=0 if st.session_state.font_size == "普通" else 1)
    selected_language = st.selectbox(language_label, ["日本語", "英語"], index=0 if st.session_state.language == "日本語" else 1)

if st.button(save_button, type="primary"):
    st.session_state.account_name = account_name.strip()
    st.session_state.account_student_no = account_student_no.strip()
    st.session_state.font_size = selected_font
    st.session_state.language = selected_language
    st.success(saved_message)
    st.rerun()

st.subheader(current_section)
st.write(f"{account_name_label}: {st.session_state.account_name or '-'}")
st.write(f"{account_student_no_label}: {st.session_state.account_student_no or '-'}")
st.write(f"{font_label}: {st.session_state.font_size}")
st.write(f"{language_label}: {st.session_state.language}")
