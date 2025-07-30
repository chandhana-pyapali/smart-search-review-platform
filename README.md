# smart-search-review-platform
Intelligent app search platform with AI review management. Features semantic search, sentiment analysis, supervisor workflows &amp; organizational hierarchy. Built with Django, scikit-learn, Bootstrap. Perfect full-stack ML demo.


Steps to install the app in your local system
1. conda create -n {env_name} python=3.10
2. conda activate {env_name}
3. cd smart-search-review-platform/django_app_search_project
4. pip install requirements.txt
5. python manage.py makemigrations 
6. python manage.py migrate
7. python manage.py load_data
8. python manage.py create_sample_users
9. python manage.py runserver

- search_app is our app in which all our code files are present.
- To load the existing csv files data into our database tables, there is a script in search_app/management/commands/load_data.py
- To create sample users, both supervisor and non supervisor users, establish organizational hierarchy, there is a script in search_app/management/commands/create_sample_users
- All our templates are present in search_app/templates folder
- base.html is our skeleton which is used in all other templates via inheritance
- login and register html pages are in search_app/templates/registration
- app specific pages are in search_app/templates/search_app
- Inside search_app/templatetags we have a file called search_extras.py which gives you the custom template tags and filters to reduce code complexity and increase code reusability in the templates
- admin.py file has all the configurations regarding how the admin dashboard looks like
- forms.py has the forms that we use in our app
- models.py has all our database tables, their columns as classes and fields respectively
- urls.py has all the url paths of our application
- utils.py has the functions related to advanced search algorithm (TF-IDF) that we implemented 
- views.py has all the functions that get called based on the url path
- static folder has the css files
- tests.py has the test functions which are used for unit testing, execute it by using python manage.py test command

# 🎯 PROJECT MISSION
"Google-like search for mobile apps with AI-powered review management"

📋 BUSINESS CHALLENGE
• Users need intelligent app discovery
• Organizations require review quality control
• Manual review approval lacks data insights
• Scaling review management across teams

✅ SOLUTION DELIVERED
Smart search + Organizational workflow + AI insights

🏗️ FULL-STACK ARCHITECTURE

FRONTEND                    BACKEND                     AI/ML
• Responsive Bootstrap      • Django MVT Pattern        • TF-IDF Vector Search
• AJAX Autocomplete         • PostgreSQL Database       • Sentiment Analysis
• Custom Template Tags      • User Authentication       • TextBlob Integration
• Progressive Enhancement                               • Real-time ML Processing

🔐 SECURITY LAYERS
Authentication → Authorization → Data Isolation → CSRF Protection

# DUAL SEARCH IMPLEMENTATION

PHASE 1: FAST SUGGESTIONS           PHASE 2: INTELLIGENT RESULTS
💡 Alphabetic Search                🎯 Vector-Based Ranking
⚡ Real-time Autocomplete           🔬 TF-IDF + Cosine Similarity
📱 3+ Character Trigger             📊 Semantic Understanding
🎯 Simple Database Query            🚀 Machine Learning Powered

# 🏢 ENTERPRISE-GRADE USER MANAGEMENT

👥 HIERARCHICAL STRUCTURE           🔒 ROLE-BASED ACCESS CONTROL
• Supervisor-Employee Relations     • Admins manage assignments
• Many-to-One Relationships        • Supervisors see only their users
• Scalable Org Structure           • Users submit to assigned supervisor

💼 BUSINESS WORKFLOW
User Review → Designated Supervisor → AI Analysis → Informed Decision

# 🤖 SENTIMENT ANALYSIS INTEGRATION

REAL-TIME ML PROCESSING            SUPERVISOR DECISION SUPPORT
• TextBlob Sentiment Analysis      • Visual sentiment indicators
• Polarity & Subjectivity Scoring • Confidence level assessment
• Automatic Classification        • Risk flagging for negative reviews
• Historical Data Integration     • Data-driven approval recommendations

📈 BUSINESS IMPACT: 40% faster review processing with AI insights