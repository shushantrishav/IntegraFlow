# IntegraFlow Dashboard

**IntegraFlow** is a lightweight, full-stack integration **dashboard** that enables users to securely connect with popular platforms like **HubSpot**, **Airtable**, and **Notion**, and fetch their data via a user-friendly web interface. It includes OAuth flows, Redis caching, a clean FastAPI backend, and a React-based frontend for interactive visualizations.

---

## 🚀 Features

- 🔐 **OAuth2 Integration**: Secure login flows for HubSpot, Airtable, and Notion  
- 📊 **Interactive Dashboard**: Connect accounts, load data, and browse via dynamic tables  
- 🧠 **Redis-Powered Caching**: Reduces duplicate API hits and speeds up data loading  
- 🧾 **Paginated Tables**: View large datasets efficiently with automatic pagination  
- 📁 **Export as JSON**: Download data directly from the UI  
- 🔁 **Connect / Disconnect** flows for flexible switching  
- 📝 **Sphinx Documentation**: Autogenerated backend docs available under `/docs`  

---

## 🧩 Tech Stack

| Layer      | Tech Used                 |
|------------|---------------------------|
| Frontend   | React + MUI               |
| Backend    | FastAPI + Python 3.10     |
| Auth       | OAuth2 (per platform)     |
| Storage    | Redis (async)             |
| Docs       | Sphinx (autodoc + rst)    |
| Logging    | Custom rotating logs      |

---

## 📚 Documentation

The complete developer and API documentation is available at:

👉 [View Documentation](https://shushantrishav.github.io/Integraflow)


---
## 🛠️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/integrafow.git
cd integraflow
```
### 2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
#### Create a .env file:
```bash
# HubSpot credentials
HUBSPOT_CLIENT_ID=your_hubspot_client_id
HUBSPOT_CLIENT_SECRET=your_hubspot_client_secret
HUBSPOT_REDIRECT_URI=http://localhost:8000/integrations/hubspot/oauth2callback
HUBSPOT_SCOPES=oauth crm.objects.contacts.read

# Notion credentials
NOTION_CLIENT_ID=your_notion_client_id
NOTION_CLIENT_SECRET=your_notion_client_secret
NOTION_REDIRECT_URI=http://localhost:8000/integrations/notion/oauth2callback

# Airtable credentials
AIRTABLE_CLIENT_ID=your_airtable_client_id
AIRTABLE_CLIENT_SECRET=your_airtable_client_secret
AIRTABLE_REDIRECT_URI=http://localhost:8000/integrations/airtable/oauth2callback

# Database credentials(Redis)
DB_HOST=localhost
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=your_db_name
```
#### Start Redis:
``` 
redis-server
```
#### Run FastAPI server:
```
uvicorn main:app --reload
```
### 3. Frontend Setup
```bash
cd frontend
npm install
npm run start
```
### 🧪 Running Tests
```
PYTHONPATH=. pytest
```
## 📷 Frontend Preview
<img width="1920" height="1826" alt="image" src="https://github.com/user-attachments/assets/f5e3b58a-896b-4d62-8b3b-fae178243e4c" />


## Documentation
#### Sphinx-generated HTML docs are available in the /docs/build/html directory after running:
```bash
cd docs
make html
```
## 🧑‍💻 Author
#### Shushant Rishav
