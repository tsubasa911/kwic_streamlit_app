import spacy
import subprocess
import sys
import importlib.util

# en_core_web_sm モデルが無ければ自動ダウンロード
try:
    spacy.load("en_core_web_sm")
except OSError:
    subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])

# モデル読み込み（ここは確実に存在している前提でOK）
nlp = spacy.load("en_core_web_sm")

# 行番号を除去する関数
def remove_line_numbers(text):
    cleaned = []
    for line in text.strip().split("\n"):
        line = line.lstrip()
        if line and line[0].isdigit():
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                cleaned.append(parts[1])
        else:
            cleaned.append(line)
    return " ".join(cleaned)

# KWIC解析関数
def keyword_in_context(text, keyword, window_size=5, context_span_length=5):
    doc = nlp(text)
    tokens = [token.text for token in doc]
    target_tokens = keyword.strip().split()
    n = len(target_tokens)

    combo_results = defaultdict(list)
    combo_counts = Counter()

    for i in range(len(doc) - n):
        window = doc[i:i + n]
        if [w.text.lower() for w in window] == [t.lower() for t in target_tokens]:
            if i + n < len(doc):
                follow = doc[i + n]
                span_end = min(len(doc), i + n + context_span_length)
                ent = "O"

                if follow.pos_ in {"PUNCT", "SYM", "SPACE"}:
                    ent = "O"
                else:
                    for ent_span in doc.ents:
                        if follow.i >= ent_span.start and follow.i < ent_span.end:
                            if (ent_span.end - ent_span.start) == 1:
                                ent = "O"
                            else:
                                ent = ent_span.label_
                            break

                key = (follow.text, follow.pos_, ent)
                left = tokens[max(0, i - window_size):i]
                right = tokens[i + n + 1:i + n + 1 + window_size]
                kwic = f"... {' '.join(left)} <span style='color:#ffcc00; font-weight:bold;'>{' '.join(t.text for t in window)}</span> {follow.text} {' '.join(right)} ..."
                combo_results[key].append(kwic)
                combo_counts[key] += 1

    return combo_counts, combo_results

# Streamlit UI
st.title("KWIC Analyzer (Token + POS + Entity)")

text_input = st.text_area("Enter your text:", height=200)
keyword = st.text_input("Enter keyword:")
window_size = st.slider("Context window size", 1, 10, 5)

if st.button("Analyze"):
    if not text_input.strip() or not keyword.strip():
        st.warning("Please enter both text and keyword.")
    else:
        cleaned_text = remove_line_numbers(text_input)
        counts, results = keyword_in_context(cleaned_text, keyword, window_size)

        if not counts:
            st.info("No matches found.")
        else:
            for (token, pos, ent), count in counts.most_common():
                st.markdown(f"""
                <div style='background:#222; color:#fff; padding:10px; margin:10px 0; border-left: 5px solid #ffcc00;'>
                    <strong style='color:#ffcc00;'>Token:</strong> {token} |
                    <strong style='color:#ffcc00;'>POS:</strong> {pos} |
                    <strong style='color:#ffcc00;'>ENTITY:</strong> {ent} |
                    <strong style='color:#ffcc00;'>Count:</strong> {count}
                </div>
                """, unsafe_allow_html=True)
                for ex in results[(token, pos, ent)]:
                    st.markdown(f"<div style='margin-left:25px; color:#eee;'>{ex}</div>", unsafe_allow_html=True)
