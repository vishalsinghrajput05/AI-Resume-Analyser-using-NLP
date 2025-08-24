AI Resume Analyser

Project Overview:
The AI Resume Analyser is a Streamlit-based web application built using Python and Natural Language Processing (NLP) that helps users evaluate their resumes and receive smart, actionable recommendations to improve them. The system provides personalized insights into resume content, highlighting strengths, weaknesses, and areas of improvement. It is designed to be user-friendly for job seekers while also featuring an admin module for tracking application usage and analyzing visitor data.

Key Features:
User Module:
Resume Upload: Users can upload their resumes in PDF/DOCX format.
NLP-Powered Analysis: The system processes resumes using NLP techniques to extract key details such as skills, experience, and education.
Smart Recommendations: Provides feedback on resume quality, missing keywords, formatting issues, and suggestions to align with industry standards.
Resume Insights: Generates a structured summary of the uploaded resume, highlighting technical and soft skills.
Experience Categorization: Classifies users into categories like Beginner, Intermediate, or Advanced based on their work experience and skill sets.

Admin Module:
Visitor Tracking: Admin can view a list of all users who have accessed the application.
Resume Management: Displays all resumes uploaded by users for review.
Data Visualization: Interactive Pie Chart showing the distribution of visitors (Beginner vs Intermediate vs Advanced).
Usage Insights: Helps admin understand the type of audience using the platform.

Tech Stack:
Frontend: Streamlit (for UI and user interaction)
Backend: Python
NLP & Analysis: SpaCy / NLTK / Scikit-learn (for keyword extraction, text classification, and recommendations)
Database: SQLite / MongoDB (for storing user and admin data)
Visualization: Matplotlib / Plotly / Streamlit Charts (for pie chart representation)

Workflow:
1. User uploads their resume.
2. NLP engine extracts and analyzes the content.
3. Application provides recommendations and categorization.
4. Data is stored and made available to the admin dashboard.
5. Admin can monitor visitors, view uploaded resumes, and analyze statistics through charts.

Impact & Use Cases:
Helps job seekers identify gaps in their resumes and improve them before applying.
Provides personalized suggestions to make resumes more industry-ready.
Allows recruiters/admins to track usage and understand the skill distribution of applicants.
Can be extended into a career counseling or recruitment platform.
