# 🅿️ Parking Token System

A comprehensive Django-based web application for managing vehicle parking operations with token-based entry and exit system.

## 🚀 Features

- **Vehicle Management**: Separate handling for 2-wheelers and 4-wheelers
- **Token-based Tracking**: Unique tokens for each parking session
- **Automated Billing**: Calculates charges based on parking duration
- **Reporting & Analytics**: Detailed entry/exit logs and financial reports
- **Admin Authentication**: Secure login system with password recovery

## 🛠️ Technology Stack

- **Backend**: Django 4.2+
- **Database**: MySQL
- **Frontend**: HTML5, CSS3, Bootstrap
- **Authentication**: Django Auth System

## 📦 Installation

```bash
# Clone repository
git clone https://github.com/Dillibabu-sys/parking-token-system.git
cd parking-token-system/server

# Setup virtual environment
python -m venv dark_evn
dark_evn\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start server
python manage.py runserver
