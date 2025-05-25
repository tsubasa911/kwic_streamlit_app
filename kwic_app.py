import streamlit as st
import spacy
import importlib.util
import subprocess
import sys

# Ensure model is installed
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    try:
        subprocess.run(
            [sys.executable, "-m", "spacy", "download", "en_core_web_sm"],
            check=True,
        )
        nlp = spacy.load("en_core_web_sm")
    except Exception:
        st.error("Failed to load or download the spaCy model.")
        st.stop()

# App title
st.title("KWIC: Keyword in Context")

# Text input
raw_text = st.text_area("Enter your text here", height=200)

# Keyword input
keyword = st.text_input("Enter a keyword to search (e.g., artificial intelligence)")

# Context window size
window_size = st.slider("Number of words to show before and after keyword", min_value=1, max_value=10, value=5)

# Run search
if st.button("Search"):
    if not raw_text or not keyword:
        st.warning("Please enter both the text and the keyword.")
    else:
        doc = nlp(raw_text)
        tokens = [token.text for token in doc]
        keyword_tokens = keyword.split()
        keyword_len = len(keyword_tokens)

        results = []
        for i in range(len(tokens) - keyword_len + 1):
            if tokens[i:i+keyword_len] == keyword_tokens:
                left = tokens[max(0, i - window_size): i]
                right = tokens[i + keyword_len: i + keyword_len + window_size]
                results.append((" ".join(left), " ".join(tokens[i:i+keyword_len]), " ".join(right)))

        if results:
            st.write(f"🔍 {len(results)} matches found.")
            for left, kw, right in results:
                st.markdown(f"... {left} **{kw}** {right} ...")
        else:
            st.info("No matches found for the given keyword.")
