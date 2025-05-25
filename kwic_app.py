import streamlit as st
import spacy
from collections import Counter

# Load spaCy model with caching
@st.cache_resource
def load_model():
    return spacy.load("en_core_web_sm")

nlp = load_model()

# Inject custom CSS for color badges and navigation bar
st.markdown("""
<style>
.badge-pos {
  background-color: #d0d0d0;
  color: black;
  border-radius: 6px;
  padding: 1px 4px;
  margin-left: 4px;
  font-size: 0.75em;
}
.badge-entity {
  background-color: #eeeeee;
  color: black;
  border-radius: 6px;
  padding: 1px 4px;
  margin-left: 4px;
  font-size: 0.75em;
}
</style>
""", unsafe_allow_html=True)

# Navigation help bar
with st.expander("📘 使い方ガイドはこちら（初めての方へ）"):
    st.markdown("""
    **KWIC Viewerの使い方：**

    1. 分析対象のテキストを貼り付ける、または.txtファイルをアップロード
    2. キーワードを入力（例：artificial intelligence）
    3. 表示モード（順序・頻度・フィルタ）を選択し、「Search」ボタンを押す
    4. 結果の中から直後の単語とその品詞・固有表現を確認できます
    """)

st.title("KWIC Viewer with POS/ENTITY Highlight")

uploaded_file = st.file_uploader("📄 Upload .txt file", type=["txt"])
raw_text = st.text_area("✍️ Or paste your text here", height=200)

text = ""
if uploaded_file:
    text = uploaded_file.read().decode("utf-8")
elif raw_text.strip():
    text = raw_text

keyword = st.text_input("🔍 Enter keyword (e.g., artificial intelligence)").strip()
window_size = st.slider("🔲 Words before and after keyword", 1, 10, 5)

mode = st.selectbox("📊 Select display mode", [
    "Sequential", "Token Frequency", "POS Frequency", "ENTITY Frequency",
    "Filter by Token", "Filter by POS", "Filter by Entity"
])

filter_value = ""
if mode.startswith("Filter"):
    filter_value = st.text_input(f"🔎 Enter value for {mode.split()[-1]}").strip()

if st.button("Search"):
    if not text or not keyword:
        st.warning("⚠️ Please provide both text and keyword.")
        st.stop()

    with st.spinner("Processing..."):
        doc = nlp(text)
        tokens = [token.text for token in doc]
        keyword_tokens = keyword.split()
        kw_len = len(keyword_tokens)

        results = []
        follow_infos = []

        for i in range(len(tokens) - kw_len):
            if tokens[i:i + kw_len] == keyword_tokens:
                left = tokens[max(0, i - window_size):i]
                right = tokens[i + kw_len:i + kw_len + window_size]

                try:
                    follow_token = doc[i + kw_len]
                    token_text = follow_token.text
                    pos = follow_token.pos_
                    ent = follow_token.ent_type_ if follow_token.ent_type_ else "O"
                except IndexError:
                    token_text, pos, ent = "", "", ""

                follow_infos.append((token_text, pos, ent))

                result = {
                    "left": " ".join(left),
                    "keyword": " ".join(keyword_tokens),
                    "follow": token_text,
                    "right": " ".join(right),
                    "pos": pos,
                    "ent": ent
                }
                results.append(result)

        if not results:
            st.info("No matches found.")
            st.stop()

        MAX_DISPLAY = 200
        results = results[:MAX_DISPLAY]

        if mode == "Token Frequency":
            grouped = Counter([r["follow"] for r in results])
            sorted_keys = [t for t, _ in grouped.most_common()]
        elif mode == "POS Frequency":
            grouped = Counter([r["pos"] for r in results])
            sorted_keys = [t for t, _ in grouped.most_common()]
        elif mode == "ENTITY Frequency":
            grouped = Counter([r["ent"] for r in results])
            sorted_keys = [t for t, _ in grouped.most_common()]
        elif mode == "Filter by Token":
            results = [r for r in results if r["follow"] == filter_value]
        elif mode == "Filter by POS":
            results = [r for r in results if r["pos"] == filter_value]
        elif mode == "Filter by Entity":
            results = [r for r in results if r["ent"] == filter_value]

        st.markdown(f"### 🔍 Showing up to {len(results)} match(es)")

        def render(r):
            kw_html = f"<span style='color:#ffffff;background:#2a9df4;padding:2px 4px;border-radius:4px;'>{r['keyword']}</span>"
            follow_html = f"<span style='background:#fff176;color:#000000;padding:2px 6px;border-radius:6px;font-weight:bold;'>{r['follow']}</span>"
            pos_html = f"<span class='badge-pos'>{r['pos']}</span>"
            ent_html = f"<span class='badge-entity'>{r['ent']}</span>"
            return f"<div style='margin-bottom:10px;'>... {r['left']} {kw_html} {follow_html} {r['right']}<br>{pos_html} {ent_html}</div>"

        if mode.startswith("Filter") or mode == "Sequential":
            for r in results:
                st.markdown(render(r), unsafe_allow_html=True)
        else:
            for key in sorted_keys:
                st.markdown(f"#### 🔹 Group: {key}")
                for r in results:
                    match = (
                        (mode == "Token Frequency" and r["follow"] == key) or
                        (mode == "POS Frequency" and r["pos"] == key) or
                        (mode == "ENTITY Frequency" and r["ent"] == key)
                    )
                    if match:
                        st.markdown(render(r), unsafe_allow_html=True)
