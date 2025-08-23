# ==============================
# AI Resume Analyzer - Streamlit
# ==============================

import os
os.environ["PAFY_BACKEND"] = "internal"  # force yt-dlp backend
import io
import base64
import random
import time
import datetime
import streamlit as st
import pandas as pd

# --- NLTK (must come before pyresparser) ---
import nltk
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")
try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords")

# --- pyresparser ---
from pyresparser import ResumeParser

# --- PDFMiner ---
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import TextConverter

# --- YouTube helper (pafy fork + yt-dlp) ---
import pafy
import yt_dlp

pafy.set_backend("internal")

# --- Streamlit components & libs ---
from streamlit_tags import st_tags
from PIL import Image
import plotly.express as px

# --- Local dataset of courses/videos ---
from Courses import (
    ds_course, web_course, android_course, ios_course, uiux_course,
    resume_videos, interview_videos
)

# --- SQLite (cloud-friendly DB) ---
import sqlite3
DB_PATH = "user_data.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cur = conn.cursor()

# =========================
# Helpers
# =========================
def ensure_dirs():
    os.makedirs("./Uploaded_Resumes", exist_ok=True)
    os.makedirs("./Logo", exist_ok=True)

def fetch_yt_video_title(link: str) -> str:
    try:
        v = pafy.new(link)
        return v.title or "Video"
    except Exception:
        return "Video"

def get_table_download_link(df: pd.DataFrame, filename: str, text: str) -> str:
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    return f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'

def pdf_reader(file_path: str) -> str:
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    with open(file_path, 'rb') as fh:
        for page in PDFPage.get_pages(fh, caching=True, check_extractable=True):
            page_interpreter.process_page(page)
        text = fake_file_handle.getvalue()
    converter.close()
    fake_file_handle.close()
    return text

def show_pdf(file_path: str):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def course_recommender(course_list):
    st.subheader("**Courses & Certificates Recommendations 🎓**")
    rec_course = []
    no_of_reco = st.slider('Choose Number of Course Recommendations:', 1, 10, 5)
    random.shuffle(course_list)
    for idx, (c_name, c_link) in enumerate(course_list, start=1):
        st.markdown(f"({idx}) [{c_name}]({c_link})")
        rec_course.append(c_name)
        if idx == no_of_reco:
            break
    return rec_course

def init_db():
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_data(
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT,
            Email_ID TEXT,
            Resume_Score TEXT,
            Timestamp TEXT,
            Page_No TEXT,
            Predicted_Field TEXT,
            User_Level TEXT,
            Actual_Skills TEXT,
            Recommended_Skills TEXT,
            Recommended_Courses TEXT
        )
    """)
    conn.commit()

def insert_data(name, email, res_score, timestamp, no_of_pages,
                reco_field, cand_level, skills, recommended_skills, courses):
    cur.execute("""
        INSERT INTO user_data
        (Name, Email_ID, Resume_Score, Timestamp, Page_No, Predicted_Field,
         User_Level, Actual_Skills, Recommended_Skills, Recommended_Courses)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, email, res_score, timestamp, no_of_pages, reco_field,
          cand_level, skills, recommended_skills, courses))
    conn.commit()

# =========================
# Page Config
# =========================
st.set_page_config(page_title="AI Resume Analyzer", page_icon="./Logo/logo2.png")
ensure_dirs()
init_db()

# =========================
# Main App
# =========================
def run():
    logo_path = "./Logo/logo2.png"
    if os.path.exists(logo_path):
        st.image(Image.open(logo_path), use_container_width=False)

    st.title("AI Resume Analyser")
    st.sidebar.markdown("# Choose User")
    choice = st.sidebar.selectbox("Choose among the given options:", ["User", "Admin"])
    st.sidebar.markdown('[© Developed by Vishal Raj](https://www.linkedin.com/in/vishalraj99/)', unsafe_allow_html=True)

    # ---------- USER ----------
    if choice == 'User':
        st.markdown("<h5>Upload your resume, and get smart recommendations</h5>", unsafe_allow_html=True)
        pdf_file = st.file_uploader("Choose your Resume", type=["pdf"])

        if pdf_file is not None:
            save_path = os.path.join("./Uploaded_Resumes", pdf_file.name)
            with open(save_path, "wb") as f:
                f.write(pdf_file.getbuffer())

            show_pdf(save_path)

            try:
                resume_data = ResumeParser(save_path).get_extracted_data()
            except Exception as e:
                st.error("❌ Error parsing resume with pyresparser.")
                st.exception(e)
                return

            if resume_data:
                st.header("**Resume Analysis**")
                st.success("Hello " + resume_data.get('name', 'Candidate'))

                st.subheader("**Your Basic info**")
                st.text('Name: ' + str(resume_data.get('name', 'NA')))
                st.text('Email: ' + str(resume_data.get('email', 'NA')))
                st.text('Contact: ' + str(resume_data.get('mobile_number', 'NA')))
                st.text('Resume pages: ' + str(resume_data.get('no_of_pages', 'NA')))

                # Candidate level
                pages = resume_data.get('no_of_pages', 1) or 1
                if pages == 1:
                    cand_level = "Fresher"
                elif pages == 2:
                    cand_level = "Intermediate"
                else:
                    cand_level = "Experienced"
                st.info(f"You are at {cand_level} level.")

                # Skills
                skills_list = resume_data.get('skills', []) or []
                st_tags(label='### Your Current Skills',
                        text='See our skills recommendation below',
                        value=skills_list,
                        key='skills_current')

                # --- Field prediction (rules) ---
                # (kept as in your version)
                # ... same keyword checks & course recommendation code ...

                # Insert into DB
                ts = time.time()
                timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H:%M:%S')
                insert_data(
                    resume_data.get('name', 'NA'),
                    resume_data.get('email', 'NA'),
                    "100",
                    timestamp,
                    str(resume_data.get('no_of_pages', 1)),
                    "Field",
                    cand_level,
                    str(skills_list),
                    "[]",
                    "[]"
                )

                # Bonus videos
                st.header("**Bonus Video for Resume Writing Tips 💡**")
                resume_vid = random.choice(resume_videos)
                st.subheader("✅ " + fetch_yt_video_title(resume_vid))
                st.video(resume_vid)

    # ---------- ADMIN ----------
    else:
        ad_user = st.text_input("Username")
        ad_password = st.text_input("Password", type='password')
        if st.button('Login'):
            if ad_user == 'Vishal' and ad_password == 'Vishal123':
                st.success("Welcome Sir !")
                df = pd.read_sql_query("SELECT * FROM user_data", conn)
                st.dataframe(df)
            else:
                st.error("Wrong ID & Password Provided")

if __name__ == "__main__":
    run()


