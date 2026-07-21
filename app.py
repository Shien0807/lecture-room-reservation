# app.py : アプリの入口（ホーム画面）
import streamlit as st

from i18n import apply_font_size, t

st.set_page_config(page_title=t("講義室予約システム", "Lecture Room Reservation"), page_icon="🏫")
apply_font_size()

st.title(t("講義室予約システム", "Lecture Room Reservation"))
st.write(t("学内の講義室を、時限（コマ）単位で予約するためのアプリです。", "This app is for reserving lecture rooms by period."))

st.subheader(t("困りごと", "Problem"))
st.write(t("空き講義室が分からず、予約の重複や口頭連絡のミスが起きていた。", "People could not quickly identify available rooms, causing duplicate reservations and communication mistakes."))

st.subheader(t("機能一覧（担当）", "Features"))
st.markdown(
    t(
        "- 一覧表示：（担当者名）\n"
        "- 登録（予約）：（担当者名）\n"
        "- 検索・絞り込み：（担当者名）\n"
        "- 予約・空き管理：（担当者名）\n"
        "- 集計・グラフ：（担当者名）",
        "- List View: (owner)\n"
        "- Registration (Reservation): (owner)\n"
        "- Search / Filter: (owner)\n"
        "- Reservation / Availability: (owner)\n"
        "- Reports / Charts: (owner)",
    )
)

st.info(t("左のサイドバーから各機能を選んでください。", "Choose a feature from the left sidebar."))

st.subheader(t("ホーム", "Home"))
st.write(t("設定つきのホーム画面から各機能へ移動できます。", "Open the settings-enabled home page and navigate to each feature."))
if st.button(t("ホーム画面を開く", "Open Home Page")):
    st.switch_page("pages/0_ホーム画面.py")
