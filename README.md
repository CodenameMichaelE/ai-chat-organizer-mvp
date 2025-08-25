
# AI Chat Organizer — MVP (Streamlit + OpenAI)

**What this is (in kid language):**
- You paste a chat.
- The app makes a **title**, **summary**, **tags**, **bullets**, and **action items** for you.
- You click **Download CSV** to save it like a spreadsheet.

## Quick Start

1) **Install tools** (one time):
```bash
pip install -r requirements.txt
```
2) **Run the app**:
```bash
streamlit run app.py
```
3) Open your browser to the link it shows (usually http://localhost:8501).
4) Paste your **OpenAI API key** inside the app.
5) Paste a chat and click **Process**.
6) Export everything from the **Export** tab as a CSV.

## Batch Mode
Paste many chats separated by a line with exactly five dashes:
```
-----
```

Example:
```
This is my first chat...
-----
This is my second chat...
```

## FAQ (Plain English)

- **Do I need coding?** No. You only paste a key and your chats.
- **Where does my data go?** It stays in your browser session and the CSV you download. The OpenAI API gets only the text you send to make the summary.
- **Can I sort and search later?** Yes. Import the CSV into Google Sheets or Notion.
- **Can we add Google Sheets auto-save?** Yes, later we can add that. This MVP keeps things simple.

## Kingdom Lens
This tool helps you **redeem time** and **bring order** to your work (Ephesians 5:16; 1 Cor. 14:40).

