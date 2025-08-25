import os
import csv
import json
import time
from typing import List, Dict, Any

import streamlit as st
import pandas as pd

# --- Optional: new OpenAI SDK (>=1.0) ---
try:
    from openai import OpenAI  # type: ignore
    HAS_OAI = True
except Exception:
    HAS_OAI = False

APP_NAME = "AI Chat Organizer — MVP"
DEFAULT_SYSTEM = """You are an expert organizer for AI chat transcripts.
Return clean, concise outputs in JSON with the following schema:
{
  "title": "string",
  "summary": "string (3-5 sentences)",
  "tags": ["kebab-case", "keywords", "max-8"],
  "bullets": ["5-8 key points"],
  "action_items": ["optional, concrete next steps"]
}
The title must be short and searchable. The summary must be faithful to the chat content.
Force tags to be 1-3 words each in kebab-case."""

DEFAULT_USER_INSTRUCTION = """Given the following chat transcript, return a single JSON object that follows the schema exactly.
If the chat covers multiple topics, pick the dominant one.
Transcript:
---
{chat}
---
Now produce ONLY the JSON, no commentary."""

def ensure_openai_client(api_key: str):
    if not HAS_OAI:
        raise RuntimeError("OpenAI SDK is not installed in this environment. Add 'openai>=1.0.0' to requirements and redeploy.")
    if not api_key:
        raise ValueError("Missing OpenAI API key.")
    os.environ["OPENAI_API_KEY"] = api_key
    return OpenAI()

def call_openai(client, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    # Use Chat Completions for broad compatibility
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=600,
        response_format={"type": "json_object"},
    )
    text = resp.choices[0].message.content
    return json.loads(text)

def process_chat(chat_text: str, client) -> Dict[str, Any]:
    system_prompt = DEFAULT_SYSTEM
    user_prompt = DEFAULT_USER_INSTRUCTION.format(chat=chat_text.strip())
    try:
        data = call_openai(client, system_prompt, user_prompt)
        # Basic validation
        for key in ["title", "summary", "tags", "bullets"]:
            if key not in data:
                raise ValueError(f"Missing key in JSON: {key}")
        # Ensure lists are lists
        data["tags"] = list(data.get("tags", []))
        data["bullets"] = list(data.get("bullets", []))
        data["action_items"] = list(data.get("action_items", []))
        return data
    except Exception as e:
        return {"error": str(e)}

def to_row(chat_text: str, result: Dict[str, Any]) -> Dict[str, Any]:
    if "error" in result:
        return {
            "date": time.strftime("%Y-%m-%d"),
            "title": "",
            "summary": result["error"],
            "tags": "",
            "bullets": "",
            "action_items": "",
            "chat_snippet": chat_text[:500] + ("..." if len(chat_text) > 500 else ""),
        }
    return {
        "date": time.strftime("%Y-%m-%d"),
        "title": result.get("title", ""),
        "summary": result.get("summary", ""),
        "tags": ", ".join(result.get("tags", [])),
        "bullets": " • ".join(result.get("bullets", [])),
        "action_items": " | ".join(result.get("action_items", [])),
        "chat_snippet": chat_text[:500] + ("..." if len(chat_text) > 500 else ""),
    }

def split_by_delimiter(text: str, delimiter: str = "\n-----\n") -> List[str]:
    parts = [p.strip() for p in text.split(delimiter)]
    return [p for p in parts if p]

def main():
    st.set_page_config(page_title=APP_NAME, page_icon="🗂️", layout="wide")
    st.title("🗂️ AI Chat Organizer — MVP")
    st.caption("Paste a chat → get a title, summary, tags, bullets, and action items. Export as CSV.")

    with st.expander("Step 0 — API Key (kept in your browser session)"):
        api_key = st.text_input("OpenAI API Key", type="password", help="Find it in your OpenAI account. We store it only in your session.")
        st.write("Model: gpt-4o-mini (change in code if desired).")

    tab_single, tab_batch, tab_export = st.tabs(["Single Chat", "Batch Paste", "Export History"])

    if "history" not in st.session_state:
        st.session_state["history"] = []  # list of rows

    # SINGLE CHAT
    with tab_single:
        st.subheader("Single Chat")
        chat = st.text_area("Paste one chat transcript here", height=250, placeholder="Paste your conversation...")
        if st.button("Process This Chat", type="primary"):
            if not chat.strip():
                st.warning("Please paste a chat first.")
            else:
                try:
                    client = ensure_openai_client(api_key)
                    result = process_chat(chat, client)
                    row = to_row(chat, result)
                    st.session_state["history"].append(row)

                    if "error" in result:
                        st.error(result["summary"])
                    else:
                        st.success("Processed! See the result below and in the Export tab.")
                        st.json(result)
                except Exception as e:
                    st.error(str(e))

    # BATCH
    with tab_batch:
        st.subheader("Batch: Multiple Chats")
        st.write("Paste multiple chats separated by a line with exactly five dashes:")
        st.code("-----", language="text")
        batch_text = st.text_area("Paste many chats", height=250, placeholder="Chat A...\n-----\nChat B...\n-----\nChat C...")
        if st.button("Process All Chats in Batch"):
            if not batch_text.strip():
                st.warning("Please paste something.")
            else:
                parts = split_by_delimiter(batch_text)
                st.info(f"Found {len(parts)} chats.")
                try:
                    client = ensure_openai_client(api_key)
                    progress = st.progress(0.0)
                    rows = []
                    for i, p in enumerate(parts, start=1):
                        result = process_chat(p, client)
                        row = to_row(p, result)
                        rows.append(row)
                        progress.progress(i / max(1, len(parts)))
                    st.session_state["history"].extend(rows)
                    st.success("Batch processing complete. See Export tab.")
                except Exception as e:
                    st.error(str(e))

    # EXPORT
    with tab_export:
        st.subheader("History & Export")
        df = pd.DataFrame(st.session_state["history"])
        if df.empty:
            st.info("No processed chats yet. Process in the other tabs first.")
        else:
            st.dataframe(df, use_container_width=True, height=400)
            csv_bytes = df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download CSV", data=csv_bytes, file_name="organized_chats.csv", mime="text/csv")
            st.write("Tip: You can import this CSV into Google Sheets or Notion for further organization.")

    with st.expander("How-To (like you're 12) — Read Me"):
       st.markdown("""
1) Get your OpenAI API key and paste it in Step 0.  
2) Copy your chat from ChatGPT (or any AI), and paste it into the Single Chat box.  
3) Click **Process**. The app will create:  
   - A short **title**  
   - A 3–5 sentence **summary**  
   - **Tags** (keywords)  
   - **Bullets** (key points)  
   - **Action Items** (optional next steps)  
4) Go to **Export History** and click **Download CSV** to save everything.  
5) Repeat for more chats, or use **Batch** to process many at once separated by `-----`.  
""")
1) Get your OpenAI API key and paste it in Step 0.
2) Copy your chat from ChatGPT (or any AI), and paste it into the Single Chat box.
3) Click **Process**. The app will create:
   - A short **title**
   - A 3-5 sentence **summary**
   - **Tags** (keywords)
   - **Bullets** (key points)
   - **Action Items** (optional next steps)
4) Go to **Export History** and click **Download CSV** to save everything.
5) Repeat for more chats, or use **Batch** to process many at once separated by `-----`.
\"\"\")

if __name__ == "__main__":
    main()
