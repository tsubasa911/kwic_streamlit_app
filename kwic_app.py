import streamlit as st
import spacy
from collections import Counter

# Load spaCy model with caching
@st.cache_resource
def load_model():
    return spacy.load("en_core_web_sm")

nlp = load_model()

# Inject custom CSS for badges and KWIC alignment
st.markdown("""
<style>
.badge-pos {
  background-color: #d0d0d0;
  color: black;
  border-radius: 6px;
  padding: 2px 6px;
  margin-right: 6px;
  font-size: 0.8em;
}
.badge-entity {
  background-color: #eeeeee;
  color: black;
  border-radius: 6px;
  padding: 2px 6px;
  font-size: 0.8em;
}
.kwic-line {
  font-family: monospace;
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
  align-items: center;
}
.kwic-index {
  width: 30px;
  text-align: right;
  color: gray;
}
.kwic-left {
  text-align: right;
  width: 40%;
  overflow-x: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.kwic-keyword {
  background-color: #2a9df4;
  color: #ffffff;
  padding: 2px 4px;
  border-radius: 4px;
  font-weight: bold;
  white-space: nowrap;
}
.kwic-follow {
  background-color: #fff176;
  color: #000000;
  padding: 2px 6px;
  border-radius: 6px;
  font-weight: bold;
  white-space: nowrap;
}
.kwic-right {
  text-align: left;
  width: 40%;
  overflow-x: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.kwic-meta {
  margin-left: 45px;
  margin-bottom: 18px;
  font-size: 0.85em;
  color: #333;
}
</style>
""", unsafe_allow_html=True)

# Help Section
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

        def render_aligned(index, r):
            return f"""
            <div class='kwic-line'>
                <div class='kwic-index'>{index+1:>3}</div>
                <div class='kwic-left'>{r['left']}</div>
                <div class='kwic-keyword'>{r['keyword']}</div>
                <div class='kwic-follow'>{r['follow']}</div>
                <div class='kwic-right'>{r['right']}</div>
            </div>
            <div class='kwic-meta'>
                <span class='badge-pos'>POS: {r['pos']}</span>
                <span class='badge-entity'>ENTITY: {r['ent']}</span>
            </div>
            """

        if mode.startswith("Filter") or mode == "Sequential":
            for i, r in enumerate(results):
                st.markdown(render_aligned(i, r), unsafe_allow_html=True)
        else:
            for key in sorted_keys:
                st.markdown(f"#### 🔹 Group: {key}")
                for i, r in enumerate(results):
                    match = (
                        (mode == "Token Frequency" and r["follow"] == key) or
                        (mode == "POS Frequency" and r["pos"] == key) or
                        (mode == "ENTITY Frequency" and r["ent"] == key)
                    )
                    if match:
                        st.markdown(render_aligned(i, r), unsafe_allow_html=True)
