# BreatheESG Backend

## Environment Variables
```bash
cp .env.example .env
# Edit .env with your actual values
```

## Install Dependencies
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run Development Server
```bash
python manage.py runserver
```

## Health Check
```
GET /api/health/
```
