import streamlit as st
import pandas as pd
import base64, random, time, datetime, io
import nltk
import os

# ---------------- NLTK Setup ----------------
# Ensure stopwords and other resources are available before pyresparser is imported
nltk_resources = {
    'stopwords': 'corpora/stopwords',
    'punkt': 'tokenizers/punkt',
    'averaged_perceptron_tagger': 'taggers/averaged_perceptron_tagger',
    'maxent_ne_chunker': 'chunkers/maxent_ne_chunker',
    'words': 'corpora/words'
}

for resource_name, resource_path in nltk_resources.items():
    try:
        nltk.data.find(resource_path)
    except LookupError:
        nltk.download(resource_name)

# ---------------- Other Imports ----------------
from pyresparser import ResumeParser
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from streamlit_tags import st_tags
from PIL import Image
import pymysql
from Courses import ds_course, web_course, android_course, ios_course, uiux_course, resume_videos, interview_videos
import plotly.express as px

# ---------------- Helper Functions ----------------
def get_table_download_link(df, filename, text):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href

def pdf_reader(file):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(fh, caching=True, check_extractable=True):
            page_interpreter.process_page(page)
        text = fake_file_handle.getvalue()
    converter.close()
    fake_file_handle.close()
    return text

def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def course_recommender(course_list):
    st.subheader("**Courses & Certificates Recommendations 🎓**")
    c = 0
    rec_course = []
    no_of_reco = st.slider('Choose Number of Course Recommendations:', 1, 10, 5)
    random.shuffle(course_list)
    for c_name, c_link in course_list:
        c += 1
        st.markdown(f"({c}) [{c_name}]({c_link})")
        rec_course.append(c_name)
        if c == no_of_reco:
            break
    return rec_course

# ---------------- Database Setup ----------------
try:
    connection = pymysql.connect(host='localhost', user='vishal', password='enter your password', db='cv')
    cursor = connection.cursor()
except Exception as e:
    st.warning("⚠️ Database not available on Streamlit Cloud. Some features may not work.")
    connection = None
    cursor = None

def insert_data(name, email, res_score, timestamp, no_of_pages, reco_field, cand_level, skills, recommended_skills, courses):
    if not cursor:
        return
    DB_table_name = 'user_data'
    insert_sql = "insert into " + DB_table_name + """ values (0,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    rec_values = (name, email, str(res_score), timestamp, str(no_of_pages), reco_field, cand_level, skills, recommended_skills, courses)
    cursor.execute(insert_sql, rec_values)
    connection.commit()

# ---------------- Streamlit Setup ----------------
st.set_page_config(page_title="AI Resume Analyzer", page_icon='./Logo/logo2.png')

def run():
    # ---------------- Safe Logo Load ----------------
    logo_path = "Logo/logo2.png"
    if os.path.exists(logo_path):
        img = Image.open(logo_path)
        st.image(img)
    else:
        st.warning("Logo image not found. Skipping display.")

    st.title("AI Resume Analyser")
    st.sidebar.markdown("# Choose User")
    activities = ["User", "Admin"]
    choice = st.sidebar.selectbox("Choose among the given options:", activities)
    link = '[©Developed by Vishal Raj](https://www.linkedin.com/in/vishalraj99/)'
    st.sidebar.markdown(link, unsafe_allow_html=True)

    # ---------------- Create DB + Table if available ----------------
    if cursor:
        cursor.execute("""CREATE DATABASE IF NOT EXISTS CV;""")
        DB_table_name = 'user_data'
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {DB_table_name}(
                ID INT NOT NULL AUTO_INCREMENT,
                Name varchar(500) NOT NULL,
                Email_ID VARCHAR(500) NOT NULL,
                resume_score VARCHAR(8) NOT NULL,
                Timestamp VARCHAR(50) NOT NULL,
                Page_no VARCHAR(5) NOT NULL,
                Predicted_Field VARCHAR(500) NOT NULL,
                User_level VARCHAR(500) NOT NULL,
                Actual_skills TEXT NOT NULL,
                Recommended_skills TEXT NOT NULL,
                Recommended_courses TEXT NOT NULL,
                PRIMARY KEY (ID)
            );
        """)

    # ---------------- User Side ----------------
    if choice == 'User':
        st.markdown('''<h5 style='text-align: left; color: #021659;'> Upload your resume, and get smart recommendations</h5>''', unsafe_allow_html=True)
        pdf_file = st.file_uploader("Choose your Resume", type=["pdf"])
        if pdf_file is not None:
            with st.spinner('Uploading your Resume...'):
                time.sleep(2)
            save_image_path = './Uploaded_Resumes/' + pdf_file.name
            with open(save_image_path, "wb") as f:
                f.write(pdf_file.getbuffer())
            show_pdf(save_image_path)
            resume_data = ResumeParser(save_image_path).get_extracted_data()
            if resume_data:
                resume_text = pdf_reader(save_image_path)
                st.header("**Resume Analysis**")
                st.success("Hello " + resume_data.get('name', 'Candidate'))
                st.subheader("**Your Basic info**")
                try:
                    st.text('Name: ' + resume_data['name'])
                    st.text('Email: ' + resume_data['email'])
                    st.text('Contact: ' + resume_data['mobile_number'])
                    st.text('Resume pages: ' + str(resume_data['no_of_pages']))
                except:
                    pass

                # ---------------- Candidate Level ----------------
                cand_level = ''
                pages = resume_data.get('no_of_pages', 1)
                if pages == 1:
                    cand_level = "Fresher"
                    st.markdown('''<h4 style='text-align: left; color: #d73b5c;'>You are at Fresher level!</h4>''', unsafe_allow_html=True)
                elif pages == 2:
                    cand_level = "Intermediate"
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>''', unsafe_allow_html=True)
                else:
                    cand_level = "Experienced"
                    st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at experience level!''', unsafe_allow_html=True)

                # ---------------- Skills Recommendation ----------------
                keywords = st_tags(label='### Your Current Skills',
                                   text='See our skills recommendation below',
                                   value=resume_data.get('skills', []), key='1')

                ds_keyword = ['tensorflow','keras','pytorch','machine learning','deep learning','flask','streamlit']
                web_keyword = ['react','django','node js','php','laravel','magento','wordpress','javascript','angular js','c#','flask']
                android_keyword = ['android','android development','flutter','kotlin','xml','kivy']
                ios_keyword = ['ios','ios development','swift','cocoa','cocoa touch','xcode']
                uiux_keyword = ['ux','adobe xd','figma','zeplin','balsamiq','ui','prototyping','wireframes','storyframes','adobe photoshop','photoshop','editing','adobe illustrator','illustrator','adobe after effects','after effects','adobe premier pro','premier pro','adobe indesign','indesign','wireframe','solid','grasp','user research','user experience']

                recommended_skills = []
                reco_field = ''
                rec_course = ''

                for i in resume_data.get('skills', []):
                    skill = i.lower()
                    if skill in ds_keyword:
                        reco_field = 'Data Science'
                        st.success("**Our analysis says you are looking for Data Science Jobs.**")
                        recommended_skills = ['Data Visualization','Predictive Analysis','Statistical Modeling','Data Mining','Clustering & Classification','Data Analytics','Quantitative Analysis','Web Scraping','ML Algorithms','Keras','Pytorch','Probability','Scikit-learn','Tensorflow',"Flask",'Streamlit']
                        st_tags(label='### Recommended skills for you.', text='Recommended skills generated from System', value=recommended_skills, key='2')
                        rec_course = course_recommender(ds_course)
                        break
                    elif skill in web_keyword:
                        reco_field = 'Web Development'
                        st.success("**Our analysis says you are looking for Web Development Jobs**")
                        recommended_skills = ['React','Django','Node JS','React JS','PHP','Laravel','Magento','Wordpress','Javascript','Angular JS','C#','Flask','SDK']
                        st_tags(label='### Recommended skills for you.', text='Recommended skills generated from System', value=recommended_skills, key='3')
                        rec_course = course_recommender(web_course)
                        break
                    elif skill in android_keyword:
                        reco_field = 'Android Development'
                        st.success("**Our analysis says you are looking for Android App Development Jobs**")
                        recommended_skills = ['Android','Android Development','Flutter','Kotlin','XML','Java','Kivy','GIT','SDK','SQLite']
                        st_tags(label='### Recommended skills for you.', text='Recommended skills generated from System', value=recommended_skills, key='4')
                        rec_course = course_recommender(android_course)
                        break
                    elif skill in ios_keyword:
                        reco_field = 'IOS Development'
                        st.success("**Our analysis says you are looking for IOS App Development Jobs**")
                        recommended_skills = ['IOS','IOS Development','Swift','Cocoa','Cocoa Touch','Xcode','Objective-C','SQLite','Plist','StoreKit',"UI-Kit",'AV Foundation','Auto-Layout']
                        st_tags(label='### Recommended skills for you.', text='Recommended skills generated from System', value=recommended_skills, key='5')
                        rec_course = course_recommender(ios_course)
                        break
                    elif skill in uiux_keyword:
                        reco_field = 'UI-UX Development'
                        st.success("**Our analysis says you are looking for UI-UX Development Jobs**")
                        recommended_skills = ['UI','User Experience','Adobe XD','Figma','Zeplin','Balsamiq','Prototyping','Wireframes','Storyframes','Adobe Photoshop','Editing','Illustrator','After Effects','Premier Pro','Indesign','Wireframe','Solid','Grasp','User Research']
                        st_tags(label='### Recommended skills for you.', text='Recommended skills generated from System', value=recommended_skills, key='6')
                        rec_course = course_recommender(uiux_course)
                        break

                # Insert data to DB
                ts = time.time()
                timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H:%M:%S')
                insert_data(resume_data.get('name','NA'), resume_data.get('email','NA'), str(sum([20]*5)), timestamp,
                              str(resume_data.get('no_of_pages',1)), reco_field, cand_level, str(resume_data.get('skills',[])),
                              str(recommended_skills), str(rec_course))

                # Bonus Videos
                st.header("**Bonus Video for Resume Writing Tips💡**")
                resume_vid = random.choice(resume_videos)
                st.subheader("✅ Bonus Resume Writing Video")
                st.video(resume_vid)

                st.header("**Bonus Video for Interview Tips💡**")
                interview_vid = random.choice(interview_videos)
                st.subheader("✅ Bonus Interview Tips Video")
                st.video(interview_vid)

    # ---------------- Admin Side ----------------
    else:
        st.success('Welcome to Admin Side')
        ad_user = st.text_input("Username")
        ad_password = st.text_input("Password", type='password')
        if st.button('Login'):
            if ad_user == 'Vishal' and ad_password == 'Enter your Password':
                st.success("Welcome Sir !")

                cursor.execute('''SELECT * FROM user_data''')
                data = cursor.fetchall()

                df = pd.DataFrame(data, columns=['ID','Name','Email','Resume Score','Timestamp','Total Page',
                                                 'Predicted Field','User Level','Actual Skills','Recommended Skills',
                                                 'Recommended Course'])
                for col in ['Predicted Field','User Level','Actual Skills','Recommended Skills','Recommended Course']:
                    df[col] = df[col].astype(str)

                st.header("**User's Data**")
                st.dataframe(df)
                st.markdown(get_table_download_link(df,'User_Data.csv','Download Report'), unsafe_allow_html=True)

                # Pie Charts
                st.subheader("**Pie-Chart for Predicted Field Recommendation**")
                fig1 = px.pie(df, names='Predicted Field', title='Predicted Field according to the Skills')
                st.plotly_chart(fig1)

                st.subheader("**Pie-Chart for User's Experienced Level**")
                fig2 = px.pie(df, names='User Level', title="Pie-Chart📈 for User's👨‍💻 Experienced Level")
                st.plotly_chart(fig2)

            else:
                st.error("Wrong ID & Password Provided")

run()
