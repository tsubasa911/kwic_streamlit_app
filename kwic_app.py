import streamlit as st
import spacy
from collections import Counter

# Load spaCy model with caching
@st.cache_resource
def load_model():
    return spacy.load("en_core_web_sm")

nlp = load_model()

# Inject CSS with color-coded POS and ENTITY badges
st.markdown("""
<style>
.badge-pos-NOUN { background-color: #3498db; color: white; }
.badge-pos-VERB { background-color: #2ecc71; color: white; }
.badge-pos-ADJ { background-color: #9b59b6; color: white; }
.badge-pos-ADV { background-color: #f39c12; color: white; }
.badge-pos-OTHER { background-color: #95a5a6; color: white; }
.badge-entity-PERSON { background-color: #e74c3c; color: white; }
.badge-entity-ORG { background-color: #e67e22; color: white; }
.badge-entity-GPE { background-color: #1abc9c; color: white; }
.badge-entity-DATE { background-color: #d35400; color: white; }
.badge-entity-O { background-color: #bdc3c7; color: white; }
.kwic-line {
  font-family: monospace;
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
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

st.title("KWIC Viewer with Color-coded POS/ENTITY and Dropdown Filters")

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

# プレフィルターの選択肢（Filter時のみ有効）
filter_value = ""
if mode in ["Filter by POS", "Filter by Entity", "Filter by Token"]:
    with st.spinner("Analyzing for available filter values..."):
        if text and keyword:
            doc = nlp(text)
            tokens = [token.text for token in doc]
            keyword_tokens = keyword.split()
            kw_len = len(keyword_tokens)

            follow_tokens = []

            for i in range(len(tokens) - kw_len):
                if tokens[i:i + kw_len] == keyword_tokens:
                    try:
                        follow_token = doc[i + kw_len]
                        follow_tokens.append(follow_token)
                    except IndexError:
                        continue

            pos_set = sorted(set(token.pos_ for token in follow_tokens))
            ent_set = sorted(set(token.ent_type_ if token.ent_type_ else "O" for token in follow_tokens))
            word_set = sorted(set(token.text for token in follow_tokens))

            if mode == "Filter by POS":
                filter_value = st.selectbox("🔎 Select POS", pos_set)
            elif mode == "Filter by Entity":
                filter_value = st.selectbox("🔎 Select ENTITY", ent_set)
            elif mode == "Filter by Token":
                filter_value = st.selectbox("🔎 Select follow token", word_set)

# 検索ボタンで実行
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

        if mode == "Filter by Token":
            results = [r for r in results if r["follow"] == filter_value]
        elif mode == "Filter by POS":
            results = [r for r in results if r["pos"] == filter_value]
        elif mode == "Filter by Entity":
            results = [r for r in results if r["ent"] == filter_value]
        elif mode == "Token Frequency":
            grouped = Counter([r["follow"] for r in results])
            sorted_keys = [t for t, _ in grouped.most_common()]
        elif mode == "POS Frequency":
            grouped = Counter([r["pos"] for r in results])
            sorted_keys = [t for t, _ in grouped.most_common()]
        elif mode == "ENTITY Frequency":
            grouped = Counter([r["ent"] for r in results])
            sorted_keys = [t for t, _ in grouped.most_common()]

        st.markdown(f"### 🔍 Showing up to {len(results)} match(es)")

        def render_aligned(index, r):
            pos_class = f"badge-pos-{r['pos']}" if r['pos'] in ["NOUN", "VERB", "ADJ", "ADV"] else "badge-pos-OTHER"
            ent_class = f"badge-entity-{r['ent']}" if r['ent'] in ["PERSON", "ORG", "GPE", "DATE"] else "badge-entity-O"
            return f"""
            <div class='kwic-line'>
                <div class='kwic-index'>{index+1:>3}</div>
                <div class='kwic-left'>{r['left']}</div>
                <div class='kwic-keyword'>{r['keyword']}</div>
                <div class='kwic-follow'>{r['follow']}</div>
                <div class='kwic-right'>{r['right']}</div>
            </div>
            <div class='kwic-meta'>
                <span class='{pos_class}'>POS: {r['pos']}</span>
                <span class='{ent_class}'>ENTITY: {r['ent']}</span>
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

# コメント：
# - 検索前にフィルター選択肢を選べるよう修正（UIの直感性向上）
