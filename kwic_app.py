import streamlit as st
import spacy

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except Exception as e:
    st.error("❌ Failed to load the spaCy model 'en_core_web_sm'. Please check your requirements.txt.")
    st.stop()

# Title
st.title("KWIC: Keyword in Context")

# Upload file
uploaded_file = st.file_uploader("Upload a .txt file", type=["txt"])

# Fallback raw text input
st.markdown("Or paste your text below:")
raw_text = st.text_area("Text input", height=200)

# Combine uploaded content if available
if uploaded_file is not None:
    file_content = uploaded_file.read().decode("utf-8")
    combined_text = file_content
else:
    combined_text = raw_text

# Keyword input
keyword = st.text_input("Enter a keyword to search (e.g., artificial intelligence)")

# Context window size
window_size = st.slider("Number of words to show before and after keyword", min_value=1, max_value=10, value=5)

# Run search
if st.button("Search"):
    if not combined_text.strip() or not keyword.strip():
        st.warning("Please provide both the text (file or input) and a keyword.")
    else:
        doc = nlp(combined_text)
        tokens = [token.text for token in doc]
        keyword_tokens = keyword.strip().split()
        keyword_len = len(keyword_tokens)

        results = []
        for i in range(len(tokens) - keyword_len + 1):
            if tokens[i:i + keyword_len] == keyword_tokens:
                left = tokens[max(0, i - window_size):i]
                right = tokens[i + keyword_len:i + keyword_len + window_size]
                results.append((" ".join(left), " ".join(tokens[i:i + keyword_len]), " ".join(right)))

        if results:
            st.success(f"🔍 Found {len(results)} match(es).")
            for left, kw, right in results:
                st.markdown(f"... {left} **{kw}** {right} ...")
        else:
            st.info("No matches found.")