import streamlit as st
import spacy
from collections import Counter

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except Exception as e:
    st.error("❌ Failed to load the spaCy model 'en_core_web_sm'.")
    st.stop()

st.title("KWIC Viewer with Enhanced Filtering & Highlighting")

# Upload and input
uploaded_file = st.file_uploader("📄 Upload .txt file", type=["txt"])
raw_text = st.text_area("✍️ Or paste your text here", height=200)

text = ""
if uploaded_file:
    text = uploaded_file.read().decode("utf-8")
elif raw_text.strip():
    text = raw_text

keyword = st.text_input("🔍 Enter keyword (e.g., artificial intelligence)").strip()
window_size = st.slider("🔲 Words before and after keyword", 1, 10, 5)

# Display mode selection
mode = st.selectbox("📊 Select display mode", [
    "Sequential", "Token Frequency", "POS Frequency", "ENTITY Frequency",
    "Filter by Token", "Filter by POS", "Filter by Entity"
])

# Filter input if applicable
filter_value = ""
if mode.startswith("Filter"):
    filter_value = st.text_input(f"🔎 Enter value for {mode.split()[-1]}").strip()

if st.button("Search"):
    if not text or not keyword:
        st.warning("⚠️ Please provide both text and keyword.")
        st.stop()

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

    # Filter or sort
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

    st.markdown(f"### 🔍 {len(results)} match(es) found")

    def render(r):
        kw_html = f"<span style='color:#ffffff;background:#2a9df4;padding:2px 4px;border-radius:4px;'>{r['keyword']}</span>"
        follow_html = f"<span style='color:#000000;background:#ffe135;padding:2px 4px;border-radius:4px;font-weight:bold;'>{r['follow']}</span>"
        pos_html = f"<span style='background:#e0e0e0;color:#333;padding:1px 4px;border-radius:4px;'>POS: {r['pos']}</span>"
        ent_html = f"<span style='background:#d0ffe0;color:#333;padding:1px 4px;border-radius:4px;'>ENTITY: {r['ent']}</span>"
        return f"... {r['left']} {kw_html} {follow_html} {r['right']}<br>{pos_html} | {ent_html}"

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
