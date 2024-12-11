import streamlit as st
import pandas as pd
import base64, random
import time, datetime
from pyresparser import ResumeParser
from pdfminer3.layout import LAParams
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer3.converter import TextConverter
import io
from streamlit_tags import st_tags
from PIL import Image
import pymysql
from Courses import ds_course, web_course, android_course, ios_course, uiux_course, resume_videos, interview_videos
import pafy
import plotly.express as px
import nltk
import spacy

# Download stopwords for NLP
nltk.download('stopwords')
custom_nlp = spacy.load("en_core_web_sm")

# YouTube video fetch function
def fetch_yt_video(link):
    video = pafy.new(link)
    return video.title

# Function to create CSV download link
def get_table_download_link(df, filename, text):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href

# PDF reader function
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

# Function to show PDF on Streamlit
def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# Course recommender function
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

# Connect to MySQL database
connection = pymysql.connect(host='localhost', user='root', password='root@123', db='ai_app')
cursor = connection.cursor()

# Insert data function for MySQL
def insert_data(name, email, res_score, timestamp, no_of_pages, reco_field, cand_level, skills, recommended_skills, courses):
    DB_table_name = 'user_data'
    insert_sql = "INSERT INTO " + DB_table_name + """ 
    (Name, Email_ID, resume_score, Timestamp, Page_no, Predicted_Field, User_level, Actual_skills, Recommended_skills, Recommended_courses) 
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    
    rec_values = (
        name, 
        email, 
        str(res_score), 
        timestamp, 
        str(no_of_pages), 
        reco_field, 
        cand_level, 
        ','.join(skills), 
        ','.join(recommended_skills), 
        ','.join(courses)
    )
    cursor.execute(insert_sql, rec_values)
    connection.commit()

# Streamlit page configuration
st.set_page_config(
   page_title="ResuMate",
   
)

def run():
    st.title("ResuMate")
    st.sidebar.markdown("# Choose User")
    activities = ["User", "Admin"]
    choice = st.sidebar.selectbox("Choose among the given options:", activities)
    st.sidebar.markdown("[FAQs](https://rejinoldjohnson.github.io/FAQ_page/) <br>", unsafe_allow_html=True)
    st.sidebar.markdown("[Testimonials](https://rejinoldjohnson.github.io/Testimonial_Page/)", unsafe_allow_html=True)
    

    # Create the DB
    db_sql = """CREATE DATABASE IF NOT EXISTS AI_APP;"""
    cursor.execute(db_sql)

    # Create table
    DB_table_name = 'user_data'
    table_sql = "CREATE TABLE IF NOT EXISTS " + DB_table_name + """
                    (ID INT NOT NULL AUTO_INCREMENT,
                     Name varchar(500) NOT NULL,
                     Email_ID VARCHAR(500) NOT NULL,
                     resume_score VARCHAR(8) NOT NULL,
                     Timestamp VARCHAR(50) NOT NULL,
                     Page_no VARCHAR(5) NOT NULL,
                     Predicted_Field BLOB NOT NULL,
                     User_level BLOB NOT NULL,
                     Actual_skills BLOB NOT NULL,
                     Recommended_skills BLOB NOT NULL,
                     Recommended_courses BLOB NOT NULL,
                     PRIMARY KEY (ID));
                    """
    cursor.execute(table_sql)

    if choice == 'User':
        st.markdown('''<h5 style='text-align: left; color: #ADD8E6;'> Upload your resume, and get smart recommendations</h5>''', unsafe_allow_html=True)
        pdf_file = st.file_uploader("Choose your Resume", type=["pdf"])
        if pdf_file is not None:
            with st.spinner('Uploading your Resume...'):
                time.sleep(4)
            save_image_path = './Uploaded_Resumes/' + pdf_file.name
            with open(save_image_path, "wb") as f:
                f.write(pdf_file.getbuffer())
            show_pdf(save_image_path)

            # Parse the resume
            resume_data = ResumeParser(save_image_path).get_extracted_data()
            if resume_data:
                resume_text = pdf_reader(save_image_path)
                st.header("**Resume Analysis**")
                st.success("Hello " + resume_data['name'])
                st.subheader("**Your Basic info**")
                
                st.text('Name: ' + resume_data['name'])
                st.text('Email: ' + resume_data['email'])
                st.text('Contact: ' + resume_data['mobile_number'])
                st.text('Resume pages: ' + str(resume_data['no_of_pages']))
                
                cand_level = ''
                if resume_data['no_of_pages'] == 1:
                    cand_level = "Fresher"
                    st.markdown('''<h4 style='text-align: left; color: #d73b5c;'>You are at Fresher level!</h4>''', unsafe_allow_html=True)
                elif resume_data['no_of_pages'] == 2:
                    cand_level = "Intermediate"
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>''', unsafe_allow_html=True)
                elif resume_data['no_of_pages'] >= 3:
                    cand_level = "Experienced"
                    st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at experience level!</h4>''', unsafe_allow_html=True)

                # Skills and Course Recommendations
                st.subheader("**Skills Recommendation 💡**")
                keywords = st_tags(label='### Your Current Skills',
                                   text='See our skills recommendation below',
                                   value=resume_data['skills'], key='1')

                ds_keyword = ['tensorflow', 'keras', 'pytorch', 'machine learning', 'deep learning', 'flask', 'streamlit']
                web_keyword = ['react', 'django', 'node js', 'php', 'wordpress', 'javascript']
                android_keyword = ['android', 'flutter', 'kotlin']
                ios_keyword = ['ios', 'swift', 'xcode']
                uiux_keyword = ['ux', 'figma', 'wireframes', 'adobe photoshop']

                recommended_skills = []
                reco_field = ''
                rec_course = ''

                # Data science recommendation
                for skill in resume_data['skills']:
                    if skill.lower() in ds_keyword:
                        reco_field = 'Data Science'
                        st.success("**Our analysis says you are looking for Data Science Jobs.**")
                        recommended_skills = ['Data Visualization', 'Predictive Analysis', 'ML Algorithms', 'Pytorch']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='2')
                        st.markdown('''<h4 style='text-align: left; color: #1ed760;'>Adding these skills to your resume will boost your job chances!</h4>''', unsafe_allow_html=True)
                        rec_course = course_recommender(ds_course)
                        break
                    # Web development recommendation
                    elif skill.lower() in web_keyword:
                        reco_field = 'Web Development'
                        st.success("**Our analysis says you are looking for Web Development Jobs.**")
                        recommended_skills = ['React', 'Node JS', 'Flask', 'JavaScript']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='3')
                        st.markdown('''<h4 style='text-align: left; color: #1ed760;'>Adding these skills to your resume will boost your job chances!</h4>''', unsafe_allow_html=True)
                        rec_course = course_recommender(web_course)
                        break
                    # Android development recommendation
                    elif skill.lower() in android_keyword:
                        reco_field = 'Android Development'
                        st.success("**Our analysis says you are looking for Android Development Jobs.**")
                        recommended_skills = ['Java', 'Kotlin', 'Flutter']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='4')
                        st.markdown('''<h4 style='text-align: left; color: #1ed760;'>Adding these skills to your resume will boost your job chances!</h4>''', unsafe_allow_html=True)
                        rec_course = course_recommender(android_course)
                        break
                    # iOS development recommendation
                    elif skill.lower() in ios_keyword:
                        reco_field = 'IOS Development'
                        st.success("**Our analysis says you are looking for IOS Development Jobs.**")
                        recommended_skills = ['Swift', 'Cocoa', 'Cocoa Touch']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='5')
                        st.markdown('''<h4 style='text-align: left; color: #1ed760;'>Adding these skills to your resume will boost your job chances!</h4>''', unsafe_allow_html=True)
                        rec_course = course_recommender(ios_course)
                        break
                    # UI/UX development recommendation
                    elif skill.lower() in uiux_keyword:
                        reco_field = 'UI-UX Development'
                        st.success("**Our analysis says you are looking for UI-UX Development Jobs.**")
                        recommended_skills = ['Adobe XD', 'Prototyping', 'Wireframes']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='6')
                        st.markdown('''<h4 style='text-align: left; color: #1ed760;'>Adding these skills to your resume will boost your job chances!</h4>''', unsafe_allow_html=True)
                        rec_course = course_recommender(uiux_course)
                        break

                # Resume score and timestamp
                st.subheader("**Resume Tips 💡**")
                resume_score = random.randint(40, 100)
                st.markdown(
                    '''<h4 style='text-align: left; color: #d73b5c;'>We rated your resume {}</h4>'''.format(resume_score),
                    unsafe_allow_html=True)
                st.markdown('''<h6 style='text-align: left; color: #021659;'>* Add more projects related to the recommended field</h6>''', unsafe_allow_html=True)
                st.markdown('''<h6 style='text-align: left; color: #021659;'>* Add links to your GitHub or portfolio</h6>''', unsafe_allow_html=True)

                # Timestamp
                ts = time.time()
                cur_time = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

                # Insert data into DB
                insert_data(resume_data['name'], resume_data['email'], resume_score, cur_time,
                            resume_data['no_of_pages'], reco_field, cand_level,
                            resume_data['skills'], recommended_skills, rec_course)

                st.balloons()

                # Add download option
                st.header("**Bonus: Resume Videos & Interview Tips 💡**")
                for video in random.sample(resume_videos, 2):
                    st.video(video)

                for interview_video in random.sample(interview_videos, 2):
                    st.video(interview_video)

    else:
        st.success('Welcome to Admin')
        ad_user = st.text_input("Username")
        ad_password = st.text_input("Password", type='password')

        if st.button('Login'):
            if ad_user == 'admin' and ad_password == 'admin@123':
                st.success("Welcome Admin")

                # Fetch user data
                cursor.execute('''SELECT * FROM user_data''')
                data = cursor.fetchall()

                st.header("**User's👨🏽‍💻 Data**")
                df = pd.DataFrame(data, columns=['ID', 'Name', 'Email', 'Resume Score', 'Timestamp', 'Page No',
                                                 'Predicted Field', 'User Level', 'Actual Skills',
                                                 'Recommended Skills', 'Recommended Courses'])
            
                # Ensure all byte columns are converted to string (if any)
                df = df.applymap(lambda x: x.decode() if isinstance(x, bytes) else x)
            
                st.dataframe(df)
                st.markdown(get_table_download_link(df, 'User_Data.csv', 'Download Report'), unsafe_allow_html=True)

                ## Admin Side Data for Visualization
                query = 'select * from user_data;'
                plot_data = pd.read_sql(query, connection)

                # Convert byte columns in plot_data to string
                plot_data = plot_data.applymap(lambda x: x.decode() if isinstance(x, bytes) else x)

                ## Pie chart for predicted field recommendations
                labels = plot_data['Predicted_Field'].unique()
                values = plot_data['Predicted_Field'].value_counts()

                st.subheader("**Pie-Chart for Predicted Field Recommendation**")
                fig = px.pie(values=values, names=labels, title='Predicted Field according to the Skills')
                st.plotly_chart(fig)

                ### Pie chart for User's👨‍💻 Experienced Level
                labels = plot_data['User_Level'].unique()
                values = plot_data['User_Level'].value_counts()

                st.subheader("**Pie-Chart for User's Experienced Level**")
                fig = px.pie(values=values, names=labels, title="Pie-Chart📈 for User's👨‍💻 Experienced Level")
                st.plotly_chart(fig)

            else:
                st.error("Wrong ID & Password Provided")

if __name__ == '__main__':
    run()
