
Backend : Python3.10 + Django

Why Django (admin interface, django rest framework)
Frontend : Node.js + Vite + tailwindcss


Setting up for services
1. UI
2. python backend services : (question, collaboration, matching) , potential another for code evaluation engine service
3. node.js backend service : (user service) -- dont rebuild the wheel


setup a python environment
- python3.10 -m venv venv
- source venv/bin/activate
- python3.10 -m pip install django
- pip3.10 freeze > requirements.txt
- pip3.10 install -r requirements.txt

creating backend services
- mkdir question_service
- django-admin startproject question_service .
- mkdir matching_service
- django-admin startproject matching_service .
- mkdir collaboration_service
- django-admin startproject collaboration_service .
