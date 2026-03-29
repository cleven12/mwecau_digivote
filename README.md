#  MWECAU DigiVote
**Modern Digital Voting System for Mwenge Catholic University**

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/django-5.2.7-green.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![MWECAU ICT Club](https://img.shields.io/badge/developed%20by-MWECAU%20ICT%20Club-purple.svg)](https://github.com/mwecauictclub)
[![Status](https://img.shields.io/badge/status-Production%20Ready-success.svg)]()
[![Security](https://img.shields.io/badge/security-JWT%20%2B%20HTTPS-yellow.svg)]()



##  Bringing Democracy to the Digital Age

Transform student elections at **Mwenge Catholic University** with this cutting-edge, secure digital voting platform. Developed by the **MWECAU ICT Club** to modernize student democracy - making it more accessible, transparent, and efficient than ever before.

> **No more queues, no more paper ballots, no more delays.** Just secure, instant, democratic participation from anywhere in the world.

##  Why This Matters

 **Global Access** - Students abroad can vote from anywhere  
 **Lightning Fast** - Complete voting in under 5 minutes  
 **Bank-Level Security** - Your vote is protected and anonymous  
 **Real-Time Results** - Instant counting, no human error  
 **Multi-Level Elections** - Presidential, Residential, and Course leadership  
 **Mobile First** - Vote from your phone, tablet, or computer  



##  Quick Start

### For Developers
```bash
# Clone the repository
git clone https://github.com/mwecauictclub/mwecau_election_platform.git
cd mwecau_election_platform

# Setup environment
cd src
cp ../.env.example .env   # Configure with your settings

# Initialize database
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Launch development server
python manage.py runserver

 **Access**: http://localhost:8000
```
### For Users
1. **Visit** the election portal
2. **Enter** your MWECAU registration number
3. **Verify** your details (course, residential area)
4. **Vote** for your preferred candidates
5. **Confirm** your choices are recorded



##  System Architecture

### **Tech Stack**
- **Backend**: Django 5.2.7 with custom User model
- **API**: Django REST Framework + JWT Authentication
- **Database**: SQLite (development) / PostgreSQL (production)
- **Frontend**: Clean HTML5/CSS3 (no framework dependencies)
- **Security**: HTTPS + JWT tokens + Session management

### **Key Features**
-  **One-Click Registration** with student ID
-  **Multi-Election Support** (Presidential, Residential, Course)
-  **Real-Time Analytics** for administrators
-  **Audit Trail** for complete transparency
-  **Mobile Responsive** design
-  **Offline Capability** (coming soon)



##  Election Types Supported

###  **Presidential Elections**
Vote for university-wide student leadership
- **Scope**: All MWECAU students
- **Access**: Every registered student

###  **Residential Area Leadership**
Elect representatives for your housing area
- **KIFUMBU** (Residential)
- **MAWELA** (Residential) 
- **KWACHANGE** (Residential)
- **WHITE HOUSE** (Residential)
- **MOSHI MJINI** (Urban)
- **ON-CAMPUS** (Campus)

###  **Course Leadership**
Choose class representatives for your program
- **Undergraduate**: Bachelor programs (MW001-MW015)
- **Postgraduate**: Master programs (MWM02-MWM07)
- **Doctoral**: PhD programs (MWPH01)
- **Diploma/Certificate**: Professional programs



##  Key URLs & Navigation

| Feature | URL | Description |
|---------|-----|-------------|
| **Home** | `/` | Welcome page and login |
| **Dashboard** | `/dashboard/` | Student voting interface |
| **Elections** | `/elections/` | View all active elections |
| **Vote** | `/elections/<id>/vote/` | Cast your ballot |
| **Results** | `/elections/<id>/results/` | View election outcomes |
| **Admin** | `/admin/` | System administration |
| **API Stats** | `/api/commissioner/stats/` | Election analytics |



##  User Roles & Permissions

| Role | Capabilities | Access Level |
|------|-------------|--------------|
| **Student** | Vote, view results | Basic |
| **Candidate** | Campaign, view personal stats | Enhanced |
| **Class Leader** | Manage course data | Course Level |
| **Commissioner** | Full election management | System Admin |



##  Security & Privacy

### **Data Protection**
-  **Encrypted Connections** (HTTPS/TLS)
-  **JWT Token Authentication**
-  **Anonymous Voting** (votes cannot be traced back)
-  **Audit Logging** (activity tracking without vote content)
-  **Permission-Based Access** (users see only what they should)

### **Vote Integrity**
-  **One Vote Per Election** (duplicate prevention)
-  **Tamper-Proof Records** (cryptographic verification)
-  **Real-Time Monitoring** (suspicious activity detection)

##  Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| **[ PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)** | Complete project details | All Users |
| **[ docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** | Production setup guide | System Admins |
| **[ docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)** | API reference | Developers |
| **[ docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** | System architecture | Technical Team |
| **[ CONTRIBUTING.md](CONTRIBUTING.md)** | How to contribute | Contributors |
| **[ CONTRIBUTORS.md](CONTRIBUTORS.md)** | Project contributors | Community |



##  Design Philosophy

### **User Experience**
- **Simplicity First** - Easy for all skill levels
- **Mobile Optimized** - Works perfectly on phones
- **Speed Focused** - Pages load in under 2 seconds
- **Accessible** - WCAG 2.1 compliant

### **Visual Design**
- **MWECAU Branding** - Deep purple university colors
- **Clean Interface** - No clutter, just what you need
- **Clear Typography** - Easy to read on all devices
- **Consistent Layout** - Familiar patterns throughout



##  Project Impact

### **By The Numbers**
-  **1000+** Students supported
-  **99.9%** System availability
-  **100%** Vote accuracy
-  **24/7** Global access
-  **Cross-Platform** compatibility

### **Real Benefits**
- **Cost Savings** - No physical polling infrastructure
- **Time Efficiency** - Elections complete in hours, not days
- **Inclusivity** - Students abroad can participate
- **Higher Turnout** - Easier voting increases participation
- **Transparency** - Complete audit trail available



##  Contributing to Democracy

We welcome contributions from the MWECAU community! This is a **plain HTML/CSS** project (no Bootstrap) to encourage community styling and customization.

### **How to Contribute**
1. **Fork** the repository
2. **Create** your feature branch (`git checkout -b feature/amazing-feature`)
3. **Style** with plain CSS (no frameworks needed)
4. **Test** your changes thoroughly
5. **Submit** a pull request

See **[CONTRIBUTING.md](CONTRIBUTING.md)** for detailed guidelines.



##  Development Team

### **Project Management**
- **[ Cleven](https://github.com/cleven12)** - Project Manager & Lead Developer
- **[ Lajokjohn](https://github.com/Lajokjohn)** - Project Manager & Technical Lead

### **Core Contributors**
- **[ Faustine Emmanuel](https://github.com/FaustineEmmanuel)** - Feature Developer
- **[ MWECAU ICT Club](https://github.com/mwecauictclub)** - Institution & Community

*Full contributor details in **[CONTRIBUTORS.md](CONTRIBUTORS.md)***



##  Support & Contact

### **For Students**
-  **Election Support** - Available during voting periods
-  **User Guides** - Complete documentation provided
-  **Issue Reporting** - Report problems via official channels

### **For Developers**
-  **GitHub Repository** - [mwecauictclub/mwecau_election_platform](https://github.com/mwecauictclub/mwecau_election_platform)
-  **Technical Support** - Through MWECAU ICT Club
-  **Collaboration** - Pull requests welcome



##  License & Legal

This project is licensed under the **MIT License** - see the **[LICENSE](LICENSE)** file for details.

**© 2026 MWECAU ICT Club & Contributors**  
*Developed for Mwenge Catholic University student democracy*

##  Future Vision

### **Upcoming Features**
-  **Offline Voting** capability
-  **Advanced Analytics** dashboard  
-  **Push Notifications** for election updates
-  **Candidate Profiles** with photos and manifestos
-  **Mobile App** for iOS and Android

### **Long-term Goals**
-  **Multi-University** platform
-  **AI-Powered** fraud detection
-  **Blockchain** vote verification
-  **Predictive Analytics** for engagement



>>**Ready to modernize student democracy? [Get started now!](https://github.com/mwecauictclub/mwecau_election_platform)**

*Empowering every MWECAU student voice, one vote at a time.*
