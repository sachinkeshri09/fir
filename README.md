# FIR Management System

A Django-based web application for managing First Information Reports (FIR) complaints.

## Features

- User authentication and registration
- FIR complaint management
- Dashboard for viewing complaints
- Multi-language support
- Contact and about pages

## Tech Stack

- **Backend**: Django 6.0.6
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript

## Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd project01
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
   - **Windows**:
     ```bash
     venv\Scripts\activate
     ```
   - **macOS/Linux**:
     ```bash
     source venv/bin/activate
     ```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Create a superuser (admin):
```bash
python manage.py createsuperuser
```

7. Run the development server:
```bash
python manage.py runserver
```

8. Open your browser and navigate to:
   ```
   http://127.0.0.1:8000/
   ```

## Project Structure

```
fir_project/          - Main Django project settings
fir_app/              - Main application
├── migrations/       - Database migrations
├── static/           - Static files (CSS, JS, images)
├── templates/        - HTML templates
├── models.py         - Database models
├── views.py          - View logic
├── urls.py           - URL routing
└── forms.py          - Django forms
```

## Environment Variables

Create a `.env` file in the root directory with:
```
DEBUG=True
SECRET_KEY=your-secret-key-here
```

## Usage

- **Admin Panel**: Visit `/admin/` and login with superuser credentials
- **User Registration**: Navigate to registration page to create a new account
- **Dashboard**: View all filed complaints after logging in

## Contributing

Feel free to submit issues and enhancement requests.

## License

This project is open source and available under the MIT License.
