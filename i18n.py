import streamlit as st


def current_language() -> str:
    return st.session_state.get("language", "日本語")


def is_english() -> bool:
    return current_language() == "英語"


def t(ja: str, en: str) -> str:
    return en if is_english() else ja


def apply_font_size() -> None:
    if st.session_state.get("font_size", "普通") == "大きい":
        st.markdown(
            """
            <style>
            p, li, label, .stMarkdown, .stSelectbox label, .stTextInput label, .stTextArea label {
                font-size: 1.15rem !important;
            }
            h1, h2, h3 {
                line-height: 1.4;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
