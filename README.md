# Medical Office Scheduler

A full-stack web application for scheduling staff in a medical GI lab, featuring AI-powered schedule generation, constraint validation, and real-time coverage tracking.

---

##  Features

### Core Functionality
- **Dual View Modes**: Weekly grid view and detailed daily timeline view
- **Staff Management**: Add, edit, and manage staff with roles, shift lengths, and preferences
- **Shift Scheduling**: Create, edit, and delete shifts with validation
- **Time-Off Management**: Submit, approve, and deny time-off requests
- **Real-Time Coverage Warnings**: Visual indicators for understaffed areas

### Advanced Features
- **AI-Powered Schedule Generation**: 
  - Generate complete weekly schedules from scratch
  - Fill empty shifts while preserving existing assignments
  - Intelligent staff rotation and constraint satisfaction
- **Constraint Validation**:
  - Prevent double-booking
  - Enforce required days off
  - Respect flexible day-off requirements
  - Area restrictions for per diem staff
  - Shift length compliance (8 or 10-hour shifts)
- **Visual Coverage Status**:
  - Green: Fully staffed
  - Orange: Understaffed with warnings
  - Red: Not staffed
- **Schedule History**: Undo/Redo functionality for easy mistake correction
- **Validation Override**: Special exception handling for unusual circumstances

---

## Tech Stack

### Frontend
- **React** (v18+) - UI framework
- **React Router** - Navigation
- **CSS3** - Styling

### Backend
- **Flask** - Python web framework
- **SQLAlchemy** - ORM for database interactions
- **PostgreSQL** - Relational database
- **Flask-Migrate** - Database migrations
- **Flask-CORS** - Cross-origin resource sharing

### AI Integration
- **OpenAI GPT-4o** - AI schedule generation
- **Python dotenv** - Environment variable management

### Testing
- **pytest** - Backend testing framework
- **pytest-flask** - Flask testing utilities

---

##  Prerequisites

- **Python 3.9+**
- **Node.js 16+** and npm
- **PostgreSQL 13+**
- **OpenAI API Key** (for AI schedule generation)

---

##  Getting an OpenAI API Key

The AI scheduling features require an OpenAI API key. Follow these steps:

### 1. Create an OpenAI Account

1. Go to https://platform.openai.com/signup
2. Sign up with your email or Google/Microsoft account
3. Verify your email address

### 2. Add Payment Method

1. Navigate to https://platform.openai.com/settings/organization/billing/overview
2. Click **"Add payment method"**
3. Enter your credit card information
4. Set a spending limit (recommended: $5-10 for testing)

**Note:** OpenAI requires a payment method even though they offer free credits for new accounts.

### 3. Generate API Key

1. Go to https://platform.openai.com/api-keys
2. Click **"Create new secret key"**
3. Give it a name (e.g., "Medical Scheduler")
4. **IMPORTANT:** Copy the key immediately - you can only see it once!
5. The key will look like: `sk-proj-...`

### 4. Add to Environment Variables

Add the key to your `backend/.env` file:
```env
OPENAI_API_KEY=sk-proj-your-actual-key-here
```

### 5. Cost Estimation

The application uses GPT-4o, which costs approximately:
- **$0.10-0.15 per schedule generation**
- **60 schedule generations ≈ $6-9**
- Set spending limits in your OpenAI dashboard to control costs

### 6. Security Best Practices

- ⚠️ **Never commit your API key to Git**
- ⚠️ Ensure `.env` is in your `.gitignore`
- ⚠️ Rotate keys if accidentally exposed
- ⚠️ Set monthly spending limits in OpenAI dashboard

---

##  Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/medical-office-scheduler.git
cd medical-office-scheduler
```

### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Setup
```bash
# Create PostgreSQL database
createdb medical_scheduler

# Run migrations
python -m flask db upgrade

# Seed with sample data (optional)
python seed.py
```

### 4. Frontend Setup
```bash
cd ../frontend

# Install dependencies
npm install
```

---

## ⚙️ Configuration

### Backend Environment Variables

Create a `.env` file in the `backend/` directory:
```env
# Database
DATABASE_URL=postgresql://localhost/medical_scheduler

# Flask
SECRET_KEY=your-secret-key-here
FLASK_ENV=development

# OpenAI (for AI scheduling)
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### Frontend Configuration

No additional configuration needed. The frontend connects to `http://127.0.0.1:5001` by default.

---

## 🏃 Running the Application

### Start Backend Server
```bash
cd backend
source venv/bin/activate
python app.py
```

Backend will run on `http://127.0.0.1:5001`

### Start Frontend Development Server
```bash
cd frontend
npm start
```

Frontend will run on `http://localhost:3000`

---

## 📖 Usage Guide

### Scheduling Workflow

1. **View Schedule**
   - Weekly view: See all areas and days at a glance
   - Daily view: Click any day for detailed timeline view

2. **Add Shifts Manually**
   - Click "+ Add Shift" button
   - Select staff, area, date, and time
   - System validates constraints automatically

3. **AI Schedule Generation**
   - **Generate Full Schedule**: Creates complete week from scratch
   - **Fill Empty Shifts**: Only fills gaps in existing schedule
   - Preview mode shows suggested shifts (greyed out with dashed border)
   - Click "Apply Schedule" to confirm or "Cancel" to discard

4. **Manage Staff**
   - Navigate to Staff Management page
   - Add new staff with roles, shift lengths, and constraints
   - Edit existing staff information
   - Activate/deactivate staff members

5. **Time-Off Requests**
   - Navigate to Time-Off page
   - Submit requests with date range and reason
   - Approve or deny pending requests
   - AI scheduling respects approved time-off

### Scheduling Rules

#### Staff Types
- **RNs (Registered Nurses)**:
  - 10-hour shifts, work 4 days/week
  - Must rotate through different areas
  - Required to work in procedure rooms periodically

- **GI Techs**:
  - 8 or 10-hour shifts
  - Rotate between procedure rooms
  - One opening tech starts at 6:00 AM

- **Scope Techs**:
  - 8-hour shifts, work 5 days/week
  - Primarily work in Scope Room
  - Can be substituted with GI Tech if unavailable

#### Area Requirements
- **Admitting**: 2 RNs (starts 6:15 AM and 6:30 AM)
- **Recovery**: 2 RNs (starts 7:00 AM and 7:30 AM)
- **Procedure Rooms 2, 3, 4**: 2 staff each (RN or GI Tech)
- **Scope Room**: 2 Scope Techs (1 GI Tech substitution allowed)

#### Constraints
- No double-booking (one shift per staff per day)
- Required days off (e.g., Sam always off Wednesday)
- Flexible days off (must be off at least one specified day)
- Area restrictions for per diem staff
- Shift length compliance (8 or 10 hours)

---

## 🗄 Database Schema

### Staff
- `id`: Primary key
- `name`: Staff member name
- `role`: RN, GI_Tech, or Scope_Tech
- `shift_length`: 8 or 10 hours
- `days_per_week`: 4 or 5
- `start_time`: Preferred start time (optional)
- `is_per_diem`: Boolean
- `area_restrictions`: JSON array of allowed areas
- `required_days_off`: JSON array of mandatory off days
- `flexible_days_off`: JSON array of flexible off days
- `is_active`: Boolean

### StaffArea
- `id`: Primary key
- `name`: Area name
- `required_rn_count`: Number of RNs needed
- `required_tech_count`: Number of GI Techs needed
- `required_scope_tech_count`: Number of Scope Techs needed
- `special_rules`: Optional text notes

### Shift
- `id`: Primary key
- `staff_id`: Foreign key to Staff
- `area_id`: Foreign key to StaffArea
- `date`: Shift date
- `start_time`: Shift start time
- `end_time`: Shift end time
- `created_at`: Timestamp

### TimeOffRequest
- `id`: Primary key
- `staff_id`: Foreign key to Staff
- `start_date`: Time-off start date
- `end_date`: Time-off end date
- `reason`: Optional reason text
- `status`: pending, approved, or denied
- `created_at`: Timestamp

---

##  API Documentation

### Staff Endpoints
```http
GET    /staff              # Get all staff
GET    /staff/<id>         # Get specific staff
POST   /staff              # Create new staff
PUT    /staff/<id>         # Update staff
DELETE /staff/<id>         # Deactivate staff
```

### Shift Endpoints
```http
GET    /shifts             # Get all shifts
GET    /shifts/<id>        # Get specific shift
POST   /shifts             # Create shift (with validation)
PUT    /shifts/<id>        # Update shift (with validation)
DELETE /shifts/<id>        # Delete shift
```

### Area Endpoints
```http
GET    /areas              # Get all areas
GET    /areas/<id>         # Get specific area
GET    /coverage/<area_id>/<date>  # Check area coverage
```

### Time-Off Endpoints
```http
GET    /time-off           # Get all time-off requests
GET    /time-off/<id>      # Get specific request
POST   /time-off           # Create request
PUT    /time-off/<id>      # Update request status
DELETE /time-off/<id>      # Delete request
```

### AI Scheduling Endpoints
```http
POST   /ai/generate-schedule    # Generate schedule suggestions
POST   /ai/apply-schedule       # Apply AI suggestions to database
```

---

##  Testing

### Run Backend Tests
```bash
cd backend
source venv/bin/activate

# Create test database
createdb medical_scheduler_test

# Run all tests
pytest -v

# Run specific test file
pytest tests/test_staff.py -v

# Run with coverage
pytest --cov=. tests/
```

### Test Coverage

Tests cover:
- Staff CRUD operations
- Shift creation and validation
- Time-off request management
- Constraint validation (double-booking, required days off)
- Coverage checking

---

## 📁 Project Structure
```
medical-office-scheduler/
├── backend/
│   ├── venv/                 # Virtual environment
│   ├── migrations/           # Database migrations
│   ├── tests/               # Backend tests
│   │   ├── conftest.py
│   │   ├── test_staff.py
│   │   ├── test_shifts.py
│   │   ├── test_validation.py
│   │   └── test_time_off.py
│   ├── app.py               # Flask application
│   ├── models.py            # SQLAlchemy models
│   ├── db.py                # Database initialization
│   ├── utils.py             # Validation utilities
│   ├── ai_scheduler.py      # AI scheduling logic
│   ├── seed.py              # Database seeding script
│   ├── requirements.txt     # Python dependencies
│   └── .env                 # Environment variables (not in git)
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ScheduleCalendar.js    # Main schedule view
│   │   │   ├── ScheduleCalendar.css
│   │   │   ├── ShiftForm.js           # Shift creation/editing
│   │   │   ├── ShiftForm.css
│   │   │   ├── StaffList.js           # Staff management
│   │   │   ├── StaffList.css
│   │   │   ├── StaffFormModal.js      # Staff form
│   │   │   ├── StaffFormModal.css
│   │   │   ├── TimeOffRequests.js     # Time-off management
│   │   │   ├── TimeOffRequests.css
│   │   │   ├── TimeOffForm.js
│   │   │   ├── TimeOffForm.css
│   │   │   ├── Navbar.js
│   │   │   └── Navbar.css
│   │   ├── App.js
│   │   ├── App.css
│   │   └── index.js
│   ├── package.json
│   └── package-lock.json
├── .gitignore
└── README.md
```

---

## 🐛 Troubleshooting

### Common Issues

**1. Database Connection Error**
```
Error: could not connect to server
```
- Ensure PostgreSQL is running: `pg_isready`
- Check database exists: `psql -l | grep medical_scheduler`
- Verify DATABASE_URL in `.env`

**2. Migration Issues**
```
Error: Target database is not up to date
```
```bash
# Reset migrations
rm -rf migrations/
python -m flask db init
python -m flask db migrate -m "Initial migration"
python -m flask db upgrade
```

**3. Frontend Can't Connect to Backend**
```
Error: Failed to fetch
```
- Ensure backend is running on port 5000
- Check CORS is enabled in `app.py`
- Verify fetch URLs use `http://127.0.0.1:5001`

**4. AI Schedule Generation Not Working**
```
Error: The api_key client option must be set
```
- Add OPENAI_API_KEY to `backend/.env`
- Restart backend server
- Verify API key is valid at https://platform.openai.com/api-keys

**5. Preview Shifts Not Showing**
- Check browser console for errors
- Verify dates match (AI uses correct year)
- Ensure area_ids and staff_ids match database

---

## 🚀 Future Enhancements

### Planned Features
- [ ] Export schedule to PDF/Excel
- [ ] Email notifications for shift assignments
- [ ] Mobile-responsive design
- [ ] Shift swap requests between staff
- [ ] Calendar integration (Google Calendar, Outlook)
- [ ] Recurring shift templates
- [ ] Shift preference system
- [ ] Overtime tracking
- [ ] Staff availability blocking

### AI Improvements
- [ ] Learning from past schedules
- [ ] Predictive staffing based on historical data
- [ ] Optimization for staff preferences
- [ ] What-if scenario analysis

---

## 📄 License

This project is licensed under the MIT License.

---

## 👥 Contributors

- Danielle Shokrian - Developer

---

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Contact: danielle.shokrian@aol.com

---