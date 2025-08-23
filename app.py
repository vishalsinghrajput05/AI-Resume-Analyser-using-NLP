# SETUP:
# 1) Keep requirements.txt in sync with these imports:
#    streamlit, pandas, nltk, pyresparser, pdfminer.six, pillow, plotly, streamlit-tags,
#    git+https://github.com/clipdalle/pafy_2023.git#egg=pafy, yt-dlp, spacy==2.3.5,
#    en_core_web_sm==2.3.1 (installed via URL in requirements)
# 2) Ensure repo has folders: ./Logo (with logo2.png) and ./Uploaded_Resumes (empty ok)

import os
import io
import base64
import random
import time
import datetime

import streamlit as st
import pandas as pd

# --- NLTK (must come before importing pyresparser) ---
import nltk
nltk.download('stopwords')
nltk.download('punkt')

# --- pyresparser (depends on spaCy 2.3.5 and en_core_web_sm 2.3.1 installed via requirements) ---
from pyresparser import ResumeParser

# --- PDFMiner ---
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import TextConverter

# --- YouTube helper (use maintained pafy fork + yt-dlp) ---
import pafy
import yt_dlp
pafy.set_backend("internal")

# --- Streamlit components & libs ---
from streamlit_tags import st_tags
from PIL import Image
import plotly.express as px

# --- Local dataset of courses/videos (must be present in repo) ---
from Courses import (
    ds_course, web_course, android_course, ios_course, uiux_course,
    resume_videos, interview_videos
)

# --- Use SQLite (cloud-friendly) instead of local MySQL ---
import sqlite3
DB_PATH = "user_data.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cur = conn.cursor()


# =========================
# Helper & Utility Functions
# =========================

def ensure_dirs():
    """Create required folders if missing."""
    os.makedirs("./Uploaded_Resumes", exist_ok=True)
    os.makedirs("./Logo", exist_ok=True)

def fetch_yt_video_title(link: str) -> str:
    """Return YouTube video title from url using pafy (yt-dlp backend)."""
    try:
        v = pafy.new(link)
        return v.title or "Video"
    except Exception:
        # Fallback to a generic label if title fetch fails (e.g., region blocking)
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
# Streamlit Page Config
# =========================

st.set_page_config(page_title="AI Resume Analyzer", page_icon="./Logo/logo2.png")
ensure_dirs()
init_db()


# =========================
# Main App
# =========================

def run():
    # Load logo from repo path (no local absolute paths)
    logo_path = "./Logo/logo2.png"
    if os.path.exists(logo_path):
        st.image(Image.open(logo_path), use_container_width=False)

    st.title("AI Resume Analyser")
    st.sidebar.markdown("# Choose User")
    activities = ["User", "Admin"]
    choice = st.sidebar.selectbox("Choose among the given options:", activities)
    link = '[© Developed by Vishal Raj](https://www.linkedin.com/in/vishalraj99/)'
    st.sidebar.markdown(link, unsafe_allow_html=True)

    # ------------- USER MODE -------------
    if choice == 'User':
        st.markdown(
            "<h5 style='text-align: left; color: #021659;'>Upload your resume, and get smart recommendations</h5>",
            unsafe_allow_html=True
        )

        pdf_file = st.file_uploader("Choose your Resume", type=["pdf"])

        if pdf_file is not None:
            with st.spinner('Uploading your Resume...'):
                time.sleep(1.5)

            save_path = os.path.join("./Uploaded_Resumes", pdf_file.name)
            with open(save_path, "wb") as f:
                f.write(pdf_file.getbuffer())

            show_pdf(save_path)

            # Extract with pyresparser
            try:
                resume_data = ResumeParser(save_path).get_extracted_data()
            except Exception as e:
                st.error(
                    "Error parsing resume with pyresparser. Ensure spaCy model installed (handled in requirements) "
                    "and that the file is a readable PDF."
                )
                st.exception(e)
                return

            if resume_data:
                resume_text = pdf_reader(save_path)
                st.header("**Resume Analysis**")
                st.success("Hello " + resume_data.get('name', 'Candidate'))
                st.subheader("**Your Basic info**")
                try:
                    st.text('Name: ' + str(resume_data.get('name', 'NA')))
                    st.text('Email: ' + str(resume_data.get('email', 'NA')))
                    st.text('Contact: ' + str(resume_data.get('mobile_number', 'NA')))
                    st.text('Resume pages: ' + str(resume_data.get('no_of_pages', 'NA')))
                except Exception:
                    pass

                # Candidate level by page count
                pages = resume_data.get('no_of_pages', 1) or 1
                if pages == 1:
                    cand_level = "Fresher"
                    st.markdown(
                        "<h4 style='text-align: left; color: #d73b5c;'>You are at Fresher level!</h4>",
                        unsafe_allow_html=True
                    )
                elif pages == 2:
                    cand_level = "Intermediate"
                    st.markdown(
                        "<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>",
                        unsafe_allow_html=True
                    )
                else:
                    cand_level = "Experienced"
                    st.markdown(
                        "<h4 style='text-align: left; color: #fba171;'>You are at experience level!</h4>",
                        unsafe_allow_html=True
                    )

                # Skills (input + tags)
                skills_list = resume_data.get('skills', []) or []
                _ = st_tags(
                    label='### Your Current Skills',
                    text='See our skills recommendation below',
                    value=skills_list,
                    key='skills_current'
                )

                # Simple rule-based field detection
                ds_keyword = ['tensorflow', 'keras', 'pytorch', 'machine learning', 'deep learning', 'flask', 'streamlit']
                web_keyword = ['react', 'django', 'node js', 'php', 'laravel', 'magento', 'wordpress', 'javascript', 'angular js', 'c#', 'flask']
                android_keyword = ['android', 'android development', 'flutter', 'kotlin', 'xml', 'kivy']
                ios_keyword = ['ios', 'ios development', 'swift', 'cocoa', 'cocoa touch', 'xcode']
                uiux_keyword = ['ux', 'adobe xd', 'figma', 'zeplin', 'balsamiq', 'ui', 'prototyping', 'wireframes', 'storyframes',
                                'adobe photoshop', 'photoshop', 'editing', 'adobe illustrator', 'illustrator',
                                'adobe after effects', 'after effects', 'adobe premier pro', 'premier pro',
                                'adobe indesign', 'indesign', 'wireframe', 'solid', 'grasp', 'user research', 'user experience']

                recommended_skills = []
                reco_field = ''
                rec_course = []

                for s in skills_list:
                    skill = (s or '').lower()
                    if skill in ds_keyword:
                        reco_field = 'Data Science'
                        st.success("**Our analysis says you are looking for Data Science Jobs.**")
                        recommended_skills = ['Data Visualization', 'Predictive Analysis', 'Statistical Modeling', 'Data Mining',
                                              'Clustering & Classification', 'Data Analytics', 'Quantitative Analysis',
                                              'Web Scraping', 'ML Algorithms', 'Keras', 'Pytorch', 'Probability',
                                              'Scikit-learn', 'Tensorflow', "Flask", 'Streamlit']
                        st_tags(label='### Recommended skills for you.',
                                text='Recommended skills generated from System',
                                value=recommended_skills, key='rec_ds')
                        rec_course = course_recommender(ds_course)
                        break
                    if skill in web_keyword:
                        reco_field = 'Web Development'
                        st.success("**Our analysis says you are looking for Web Development Jobs.**")
                        recommended_skills = ['React', 'Django', 'Node JS', 'React JS', 'PHP', 'Laravel', 'Magento',
                                              'Wordpress', 'Javascript', 'Angular JS', 'C#', 'Flask', 'SDK']
                        st_tags(label='### Recommended skills for you.',
                                text='Recommended skills generated from System',
                                value=recommended_skills, key='rec_web')
                        rec_course = course_recommender(web_course)
                        break
                    if skill in android_keyword:
                        reco_field = 'Android Development'
                        st.success("**Our analysis says you are looking for Android App Development Jobs.**")
                        recommended_skills = ['Android', 'Android Development', 'Flutter', 'Kotlin', 'XML', 'Java',
                                              'Kivy', 'GIT', 'SDK', 'SQLite']
                        st_tags(label='### Recommended skills for you.',
                                text='Recommended skills generated from System',
                                value=recommended_skills, key='rec_android')
                        rec_course = course_recommender(android_course)
                        break
                    if skill in ios_keyword:
                        reco_field = 'IOS Development'
                        st.success("**Our analysis says you are looking for IOS App Development Jobs.**")
                        recommended_skills = ['IOS', 'IOS Development', 'Swift', 'Cocoa', 'Cocoa Touch', 'Xcode',
                                              'Objective-C', 'SQLite', 'Plist', 'StoreKit', "UI-Kit", 'AV Foundation',
                                              'Auto-Layout']
                        st_tags(label='### Recommended skills for you.',
                                text='Recommended skills generated from System',
                                value=recommended_skills, key='rec_ios')
                        rec_course = course_recommender(ios_course)
                        break
                    if skill in uiux_keyword:
                        reco_field = 'UI-UX Development'
                        st.success("**Our analysis says you are looking for UI-UX Development Jobs.**")
                        recommended_skills = ['UI', 'User Experience', 'Adobe XD', 'Figma', 'Zeplin', 'Balsamiq',
                                              'Prototyping', 'Wireframes', 'Storyframes', 'Adobe Photoshop', 'Editing',
                                              'Illustrator', 'After Effects', 'Premier Pro', 'Indesign', 'Wireframe',
                                              'Solid', 'Grasp', 'User Research']
                        st_tags(label='### Recommended skills for you.',
                                text='Recommended skills generated from System',
                                value=recommended_skills, key='rec_uiux')
                        rec_course = course_recommender(uiux_course)
                        break

                # Insert data into DB
                ts = time.time()
                timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H:%M:%S')
                resume_score = str(sum([20] * 5))  # simple fixed scoring (100)
                insert_data(
                    resume_data.get('name', 'NA'),
                    resume_data.get('email', 'NA'),
                    resume_score,
                    timestamp,
                    str(resume_data.get('no_of_pages', 1)),
                    reco_field,
                    cand_level,
                    str(skills_list),
                    str(recommended_skills),
                    str(rec_course)
                )

                # Bonus Videos
                st.header("**Bonus Video for Resume Writing Tips 💡**")
                resume_vid = random.choice(resume_videos)
                st.subheader("✅ " + fetch_yt_video_title(resume_vid))
                st.video(resume_vid)

                st.header("**Bonus Video for Interview Tips 💡**")
                interview_vid = random.choice(interview_videos)
                st.subheader("✅ " + fetch_yt_video_title(interview_vid))
                st.video(interview_vid)

    # ------------- ADMIN MODE -------------
    else:
        st.success('Welcome to Admin Side')
        ad_user = st.text_input("Username")
        ad_password = st.text_input("Password", type='password')
        if st.button('Login'):
            if ad_user == 'Vishal' and ad_password == 'Vishal123':
                st.success("Welcome Sir !")

                df = pd.read_sql_query("SELECT * FROM user_data", conn)
                # Rename columns for nicer display
                rename_map = {
                    'Resume_Score': 'Resume Score',
                    'Email_ID': 'Email',
                    'Page_No': 'Total Page',
                    'Predicted_Field': 'Predicted Field',
                    'User_Level': "User Level",
                    'Actual_Skills': 'Actual Skills',
                    'Recommended_Skills': 'Recommended Skills',
                    'Recommended_Courses': 'Recommended Course'
                }
                df_display = df.rename(columns=rename_map)

                st.header("**User's Data**")
                st.dataframe(df_display)

                st.markdown(get_table_download_link(df_display, 'User_Data.csv', 'Download Report'),
                            unsafe_allow_html=True)

                # Pie Charts
                st.subheader("**Pie-Chart for Predicted Field Recommendation**")
                if 'Predicted Field' in df_display.columns and not df_display['Predicted Field'].isna().all():
                    fig1 = px.pie(df_display, names='Predicted Field',
                                  title='Predicted Field according to the Skills')
                    st.plotly_chart(fig1, use_container_width=True)
                else:
                    st.info("No Predicted Field data yet to chart.")

                st.subheader("**Pie-Chart for User's Experienced Level**")
                if "User Level" in df_display.columns and not df_display["User Level"].isna().all():
                    fig2 = px.pie(df_display, names='User Level',
                                  title="Pie-Chart 📈 for User's 👨‍💻 Experienced Level")
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.info("No User Level data yet to chart.")

            else:
                st.error("Wrong ID & Password Provided")


if __name__ == "__main__":
    run()

