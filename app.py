# app.py
import os
import streamlit as st
from dotenv import load_dotenv
from datetime import datetime
load_dotenv()

st.set_page_config(page_title="AI Research & Notes Assistant", layout="wide")
st.title("AI Research & Notes Assistant")

# --- Light DB & utils imports (kept) ---
from database.db import insert_note, get_all_notes, db, test_connection
from models.note_model import create_note
from utils.file_utils import extract_text_from_pdf, extract_text_from_txt, extract_text_with_ocr
# removed save_text_as_pdf (not used anymore)

# --- Core remaining services ---
from services.ai_service import generate_summary, answer_question, ieee_review
from services.user_service import register_user, login_user
from services.writing_service import generate_abstract, generate_introduction, generate_conclusion, generate_custom_section
from services.grammar_service import grammar_check_report
from services.study_service import generate_flashcards, generate_practice_questions
from services.formatter_service import ieee_auto_format, ieee_sectionify
# removed export_service
from services.tag_service import add_tags_to_note, get_notes_by_tag
import services.citation_checker as citation_checker

# Ensure session_state user exists
if "user" not in st.session_state:
    st.session_state.user = None

# Sidebar DB connection
try:
    st.sidebar.success(test_connection())
except Exception:
    st.sidebar.error("MongoDB connection test failed. Check .env and Atlas network settings.")

# -------------------------
# AUTHENTICATION (SIDEBAR)
# -------------------------
st.sidebar.title("🔑 User Authentication")
if not st.session_state.user:
    auth_choice = st.sidebar.radio("Choose", ["Login", "Register"])
    email = st.sidebar.text_input("Email", key="auth_email")
    password = st.sidebar.text_input("Password", type="password", key="auth_password")

    if auth_choice == "Register":
        name = st.sidebar.text_input("Name", key="auth_name")
        if st.sidebar.button("Register"):
            if not name or not email or not password:
                st.sidebar.error("Please fill all fields.")
            else:
                success, msg = register_user(name, email, password)
                if success:
                    st.sidebar.success(msg)
                    success_login, user = login_user(email, password)
                    if success_login:
                        st.session_state.user = user
                        st.sidebar.success("Logged in as " + user["name"])
                else:
                    st.sidebar.error(msg)

    elif auth_choice == "Login":
        if st.sidebar.button("Login"):
            success, user = login_user(email, password)
            if success:
                st.session_state.user = user
                st.sidebar.success("✅ Logged in successfully")
            else:
                st.sidebar.error(user)
else:
    st.sidebar.success(f"Welcome {st.session_state.user['name']}")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.experimental_rerun()

if not st.session_state.user:
    st.info("Please register or log in (sidebar) to continue.")
    st.stop()

# -------------------------
# MAIN MENU
# -------------------------
menu_items = [
    "Upload Notes", "View Notes", "Generate Summary", "AI Q&A",
    "IEEE Documentation Review", "Citation Checker",
    "AI Writing Assistant", "Grammar & Readability Checker",
    "Study Mode (Flashcards)", "IEEE Auto-Formatter",
    "Advanced Search (Tags)", "My Account"
]
choice = st.sidebar.radio("Go to", menu_items)

# -------------------------
# UPLOAD NOTES
# -------------------------
if choice == "Upload Notes":
    st.header("📤 Upload Research Notes")
    title = st.text_input("Title")
    uploaded_file = st.file_uploader("Upload file (txt, pdf)", type=["txt", "pdf"])

    if uploaded_file and st.button("Upload and Save"):
        content = ""
        try:
            if uploaded_file.type == "application/pdf":
                content = extract_text_from_pdf(uploaded_file)
                if not content:
                    uploaded_file.seek(0)
                    content = extract_text_with_ocr(uploaded_file)
            else:
                content = extract_text_from_txt(uploaded_file)
        except Exception as e:
            st.error(f"Error extracting file: {e}")
            content = ""

        if not content.strip():
            st.error("Could not extract text from the file.")
        else:
            note = create_note(title, content, summary=None)
            note["user_id"] = st.session_state.user["_id"]
            note_id = insert_note(note)
            st.success(f"✅ Note saved with ID: {note_id}")

# -------------------------
# VIEW NOTES
# -------------------------
elif choice == "View Notes":
    st.header("📚 My Notes")
    notes = list(db.notes.find({"user_id": st.session_state.user["_id"]}).sort("created_at", -1))
    if not notes:
        st.info("No notes found. Upload notes to get started.")
    else:
        for note in notes:
            with st.expander(note["title"]):
                st.write(note.get("content", "")[:5000])
                if note.get("summary"):
                    st.markdown("**AI Summary:**")
                    st.write(note["summary"])
                tags = note.get("tags", [])
                st.write("Tags:", ", ".join(tags) if tags else "No tags")
                col1, col2, col3 = st.columns(3)
                if col1.button("📝 Edit title", key=f"edit_{note['_id']}"):
                    new_title = st.text_input("New title", value=note["title"], key=f"nt_{note['_id']}")
                    if st.button("Save title", key=f"save_title_{note['_id']}"):
                        db.notes.update_one({"_id": note["_id"]}, {"$set": {"title": new_title}})
                        st.success("Title updated.")
                        st.experimental_rerun()
                if col2.button("🏷️ Add/Update tags", key=f"tag_{note['_id']}"):
                    new_tags = st.text_input("Comma-separated tags", value=",".join(tags), key=f"tags_in_{note['_id']}")
                    if st.button("Save tags", key=f"save_tags_{note['_id']}"):
                        tag_list = [t.strip() for t in new_tags.split(",") if t.strip()]
                        add_tags_to_note(note["_id"], tag_list)
                        st.success("Tags saved.")
                        st.experimental_rerun()
                if col3.button("🗑️ Delete note", key=f"del_{note['_id']}"):
                    db.notes.delete_one({"_id": note["_id"], "user_id": st.session_state.user["_id"]})
                    st.warning("Note deleted.")
                    st.experimental_rerun()

# -------------------------
# GENERATE SUMMARY
# -------------------------
elif choice == "Generate Summary":
    st.header("📝 AI Summarization")
    notes = list(db.notes.find({"user_id": st.session_state.user["_id"]}))
    if not notes:
        st.info("No notes available.")
    else:
        titles = [n["title"] for n in notes]
        selected = st.selectbox("Select Note", titles)
        note = next(n for n in notes if n["title"] == selected)
        if st.button("Generate Summary"):
            with st.spinner("Generating summary..."):
                summary = generate_summary(note["content"])
                db.notes.update_one({"_id": note["_id"]}, {"$set": {"summary": summary}})
                st.success("Summary saved to note.")
                st.write(summary)

# -------------------------
# AI Q&A
# -------------------------
elif choice == "AI Q&A":
    st.header("💡 Ask AI about your Notes")
    notes = list(db.notes.find({"user_id": st.session_state.user["_id"]}))
    if not notes:
        st.info("No notes available.")
    else:
        selected = st.selectbox("Select Note", [n["title"] for n in notes])
        note = next(n for n in notes if n["title"] == selected)
        question = st.text_input("Ask a question about this note")
        if st.button("Get Answer") and question.strip():
            with st.spinner("Getting answer..."):
                answer = answer_question(note["content"], question)
                st.subheader("Answer")
                st.write(answer)
                db.queries.insert_one({
                    "note_id": note["_id"],
                    "user_id": st.session_state.user["_id"],
                    "question": question,
                    "answer": answer,
                    "type": "qa",
                    "created_at": datetime.utcnow()
                })

# -------------------------
# IEEE DOCUMENTATION REVIEW
# -------------------------
elif choice == "IEEE Documentation Review":
    st.header("📄 IEEE Documentation Review (AI)")
    uploaded_file = st.file_uploader("Upload Documentation (PDF/TXT)", type=["txt", "pdf"])
    if uploaded_file and st.button("Review with IEEE Standards"):
        content = ""
        if uploaded_file.type == "application/pdf":
            content = extract_text_from_pdf(uploaded_file)
            if not content:
                uploaded_file.seek(0)
                content = extract_text_with_ocr(uploaded_file)
        else:
            content = extract_text_from_txt(uploaded_file)

        if not content.strip():
            st.error("Could not extract text.")
        else:
            with st.spinner("Running IEEE review..."):
                suggestions = ieee_review(content)
                st.subheader("Suggestions")
                st.write(suggestions)
                db.queries.insert_one({
                    "user_id": st.session_state.user["_id"],
                    "note_type": "ieee_doc",
                    "document": content,
                    "review": suggestions,
                    "type": "ieee_review",
                    "created_at": datetime.utcnow()
                })

# -------------------------
# CITATION CHECKER
# -------------------------
elif choice == "Citation Checker":
    st.header("📖 Citation & Reference Checker")
    uploaded_file = st.file_uploader("Upload Documentation (PDF/TXT)", type=["txt", "pdf"])
    if uploaded_file and st.button("Check References"):
        content = ""
        if uploaded_file.type == "application/pdf":
            content = extract_text_from_pdf(uploaded_file)
            if not content:
                uploaded_file.seek(0)
                content = extract_text_with_ocr(uploaded_file)
        else:
            content = extract_text_from_txt(uploaded_file)

        if not content.strip():
            st.error("Could not extract text.")
        else:
            results = citation_checker.check_references(content)
            st.subheader("Reference Issues")
            for r in results:
                st.write("- " + r)
            db.queries.insert_one({
                "user_id": st.session_state.user["_id"],
                "note_type": "citation_check",
                "document_excerpt": content[:2000],
                "citations": results,
                "type": "citation",
                "created_at": datetime.utcnow()
            })

# -------------------------
# AI WRITING ASSISTANT
# -------------------------
elif choice == "AI Writing Assistant":
    st.header("🖊️ AI Writing Assistant (IEEE-style)")
    notes = list(db.notes.find({"user_id": st.session_state.user["_id"]}))
    source_option = st.radio("Source", ["Paste text", "Use saved note"])
    source_text = ""
    if source_option == "Paste text":
        source_text = st.text_area("Paste your paper/notes here", height=250)
    else:
        if not notes:
            st.info("No saved notes.")
        else:
            sel = st.selectbox("Select note", [n["title"] for n in notes])
            note = next(n for n in notes if n["title"] == sel)
            source_text = note["content"]

    section_choice = st.selectbox("Section to generate", ["Abstract", "Introduction", "Conclusion", "Custom Section"])
    if section_choice == "Custom Section":
        custom_title = st.text_input("Custom section title")
    else:
        custom_title = None

    if st.button("Generate Section") and source_text.strip():
        with st.spinner("Generating..."):
            if section_choice == "Abstract":
                out = generate_abstract(source_text, max_words=200)
            elif section_choice == "Introduction":
                out = generate_introduction(source_text, max_paragraphs=3)
            elif section_choice == "Conclusion":
                out = generate_conclusion(source_text, max_sentences=6)
            else:
                out = generate_custom_section(custom_title or "Section", source_text)

            st.subheader("Generated Text")
            st.write(out)
            db.queries.insert_one({
                "user_id": st.session_state.user["_id"],
                "type": "writing_assistant",
                "section": section_choice if section_choice != "Custom Section" else custom_title,
                "result": out,
                "created_at": datetime.utcnow()
            })

# -------------------------
# GRAMMAR & READABILITY
# -------------------------
elif choice == "Grammar & Readability Checker":
    st.header("✍️ Grammar & Readability Checker")
    uploaded_file = st.file_uploader("Upload doc (PDF/TXT) or paste text", type=["txt", "pdf"])
    paste_text = st.text_area("OR paste text here", height=200)
    if st.button("Check & Improve"):
        content = paste_text.strip()
        if not content and uploaded_file:
            content = extract_text_from_pdf(uploaded_file) if uploaded_file.type == "application/pdf" else extract_text_from_txt(uploaded_file)
            if not content.strip():
                uploaded_file.seek(0)
                content = extract_text_with_ocr(uploaded_file) if uploaded_file.type == "application/pdf" else ""
        if not content.strip():
            st.error("No text provided.")
        else:
            with st.spinner("Checking..."):
                report = grammar_check_report(content)
                st.subheader("Grammar Issues (LanguageTool)")
                if report["grammar_issues"]:
                    for m in report["grammar_issues"]:
                        suggestions = ", ".join(m["suggestions"][:3]) if m["suggestions"] else "No suggestions"
                        st.write(f"- {m['error']} — Suggestions: {suggestions}")
                else:
                    st.success("No grammar issues found.")
                st.subheader("Improved Version (AI)")
                st.write(report["improved_text"])
                db.queries.insert_one({
                    "user_id": st.session_state.user["_id"],
                    "type": "grammar_check",
                    "result": report,
                    "created_at": datetime.utcnow()
                })

# -------------------------
# STUDY MODE (FLASHCARDS)
# -------------------------
elif choice == "Study Mode (Flashcards)":
    st.header("📚 Study Mode - Flashcards & Practice Questions")
    uploaded_file = st.file_uploader("Upload notes (TXT/PDF) or select saved note", type=["txt", "pdf"])
    notes = list(db.notes.find({"user_id": st.session_state.user["_id"]}))
    note_text = ""
    if notes:
        use_saved = st.checkbox("Use saved note")
        if use_saved:
            sel = st.selectbox("Select saved note", [n["title"] for n in notes])
            note_text = next(n for n in notes if n["title"] == sel)["content"]
    if uploaded_file and not note_text:
        note_text = extract_text_from_pdf(uploaded_file) if uploaded_file.type == "application/pdf" else extract_text_from_txt(uploaded_file)
        if not note_text.strip():
            uploaded_file.seek(0)
            note_text = extract_text_with_ocr(uploaded_file)
    if st.button("Generate Flashcards") and note_text.strip():
        with st.spinner("Generating flashcards..."):
            cards = generate_flashcards(note_text, num_cards=8)
            st.subheader("Flashcards")
            for i, c in enumerate(cards):
                if "error" in c:
                    st.error(c["error"])
                else:
                    st.markdown(f"**Q{i+1}:** {c['question']}")
                    st.markdown(f"**A{i+1}:** {c['answer']}")
            db.queries.insert_one({
                "user_id": st.session_state.user["_id"],
                "type": "flashcards",
                "result": cards,
                "created_at": datetime.utcnow()
            })
    if st.button("Generate Practice Questions") and note_text.strip():
        with st.spinner("Generating questions..."):
            qs = generate_practice_questions(note_text, num_questions=8)
            st.subheader("Practice Questions")
            for q in qs:
                st.write("- " + q)
            db.queries.insert_one({
                "user_id": st.session_state.user["_id"],
                "type": "practice_questions",
                "result": qs,
                "created_at": datetime.utcnow()
            })

# -------------------------
# IEEE AUTO-FORMATTER
# -------------------------
elif choice == "IEEE Auto-Formatter":
    st.header("📄 IEEE Auto-Formatter")
    uploaded_file = st.file_uploader("Upload project doc (PDF/TXT)", type=["txt", "pdf"])
    notes = list(db.notes.find({"user_id": st.session_state.user["_id"]}))
    use_saved = st.checkbox("Or use saved note")
    content = ""
    if use_saved and notes:
        sel = st.selectbox("Select saved note", [n["title"] for n in notes])
        content = next(n for n in notes if n["title"] == sel)["content"]
    elif uploaded_file:
        content = extract_text_from_pdf(uploaded_file) if uploaded_file.type == "application/pdf" else extract_text_from_txt(uploaded_file)
        if not content.strip():
            uploaded_file.seek(0)
            content = extract_text_with_ocr(uploaded_file)
    if st.button("Auto-Format to IEEE") and content.strip():
        with st.spinner("Formatting..."):
            formatted = ieee_auto_format(content)
            st.subheader("Formatted Draft")
            st.write(formatted)
            db.queries.insert_one({
                "user_id": st.session_state.user["_id"],
                "type": "ieee_format",
                "result": formatted,
                "created_at": datetime.utcnow()
            })

# -------------------------
# ADVANCED SEARCH (TAGS)
# -------------------------
elif choice == "Advanced Search (Tags)":
    st.header("🔎 Advanced Search (Tags)")
    tag = st.text_input("Search by tag (exact match)")
    if st.button("Search by tag") and tag.strip():
        hits = get_notes_by_tag(str(st.session_state.user["_id"]), tag.strip())
        if not hits:
            st.info("No notes found with that tag.")
        else:
            for h in hits:
                st.markdown(f"**{h['title']}**")
                st.write(h.get("content", "")[:1000])

# -------------------------
# MY ACCOUNT
# -------------------------
elif choice == "My Account":
    st.header("⚙️ My Dashboard")
    st.write("Manage profile, view stats, and control your account.")

    st.subheader("👤 Profile Settings")
    name = st.text_input("Name", value=st.session_state.user["name"])
    email = st.text_input("Email", value=st.session_state.user["email"])
    new_password = st.text_input("New Password (leave blank to keep current)", type="password")
    if st.button("Update Profile"):
        update_data = {"name": name, "email": email}
        if new_password.strip():
            import bcrypt
            hashed = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())
            update_data["password"] = hashed
        db.users.update_one({"_id": st.session_state.user["_id"]}, {"$set": update_data})
        st.session_state.user.update(update_data)
        st.success("Profile updated")

    st.markdown("---")
    st.subheader("📊 Statistics")
    num_notes = db.notes.count_documents({"user_id": st.session_state.user["_id"]})
    num_queries = db.queries.count_documents({"user_id": st.session_state.user["_id"]})
    st.metric("Notes Uploaded", num_notes)
    st.metric("Queries Made", num_queries)

    st.markdown("---")
    st.subheader("📜 Recent Activity")
    activities = list(db.queries.find({"user_id": st.session_state.user["_id"]}).sort("created_at", -1).limit(8))
    if activities:
        for a in activities:
            t = a.get("created_at")
            typ = a.get("type", "action")
            desc = a.get("question") or a.get("note_type") or a.get("type") or ""
            st.write(f"- [{t}] {typ} — {desc}")
    else:
        st.info("No recent activity.")

    st.markdown("---")
    st.subheader("🗑️ Danger Zone")
    if st.button("Delete All My Notes"):
        db.notes.delete_many({"user_id": st.session_state.user["_id"]})
        st.warning("All notes deleted.")
    if st.button("Delete My Account (Permanent)"):
        db.users.delete_one({"_id": st.session_state.user["_id"]})
        db.notes.delete_many({"user_id": st.session_state.user["_id"]})
        db.queries.delete_many({"user_id": st.session_state.user["_id"]})
        st.session_state.user = None
        st.experimental_rerun()
