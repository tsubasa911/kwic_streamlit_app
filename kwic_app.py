import streamlit as st
import spacy

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except Exception as e:
    st.error("❌ Failed to load the spaCy model 'en_core_web_sm'. Please check your requirements.txt.")
    st.stop()

# --- App Layout ---
st.title("KWIC Viewer with POS/Entity Insight")

st.markdown("#### Upload a .txt file or enter text below:")
uploaded_file = st.file_uploader("📄 Upload .txt file", type=["txt"])
raw_text = st.text_area("✍️ Or paste text here", height=200)

text = ""
if uploaded_file is not None:
    text = uploaded_file.read().decode("utf-8")
elif raw_text.strip():
    text = raw_text

# --- Keyword and Window ---
keyword = st.text_input("🔍 Enter keyword (e.g., artificial intelligence)")
window_size = st.slider("🔲 Number of words before and after keyword", 1, 10, 5)

# --- Search ---
if st.button("Search"):
    if not text.strip() or not keyword.strip():
        st.warning("⚠️ Please provide both text and keyword.")
        st.stop()

    doc = nlp(text)
    tokens = [token.text for token in doc]
    keyword_tokens = keyword.strip().split()
    kw_len = len(keyword_tokens)

    results = []
    for i in range(len(tokens) - kw_len):
        if tokens[i:i + kw_len] == keyword_tokens:
            left = tokens[max(0, i - window_size):i]
            right = tokens[i + kw_len:i + kw_len + window_size]

            # Highlight keyword
            kw_html = f"<span style='color:#ffffff; background:#2a9df4; padding:2px 4px; border-radius:4px;'>{' '.join(keyword_tokens)}</span>"

            # Highlight next token with POS/Entity
            try:
                follow_token = doc[i + kw_len]
                follow_html = f"<span style='color:#000000; background:#ffe135; padding:2px 4px; border-radius:4px; font-weight:bold;'>{follow_token.text}</span>"
                pos = follow_token.pos_
                ent = follow_token.ent_type_ if follow_token.ent_type_ else "O"
                tag_info = f"<sub><i>POS: {pos} | ENTITY: {ent}</i></sub>"
            except IndexError:
                follow_html = ""
                tag_info = ""

            result_html = (
                f"<div style='padding:6px 0;'>... "
                f"{' '.join(left)} "
                f"{kw_html} "
                f"{follow_html} "
                f"{' '.join(right)}"
                f"<br>{tag_info}</div>"
            )

            results.append(result_html)

    # --- Display ---
    if results:
        st.success(f"✅ {len(results)} match(es) found.")
        for html in results:
            st.markdown(html, unsafe_allow_html=True)
    else:
        st.info("No matches found.")
