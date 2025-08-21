# MWECAU Election Platform

A comprehensive digital voting system designed for Mwenge Catholic University (MWECAU) to facilitate transparent and secure student elections.

## 📋 Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Technology Stack](#technology-stack)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing](#contributing)
- [Documentation](#documentation)
- [Contact](#contact)
- [License](#license)

## 🎯 Overview

The MWECAU Election Platform is a modern web-based voting system that enables secure, transparent, and efficient student elections at Mwenge Catholic University. The platform provides a complete solution for managing electoral processes, from candidate registration to vote counting and result publication.

### Key Features

- **Secure Authentication**: Student verification and secure login system
- **Candidate Management**: Registration and profile management for candidates
- **Real-time Voting**: Live voting with instant result updates
- **Result Analytics**: Comprehensive reporting and data visualization
- **Admin Dashboard**: Complete election management interface
- **Mobile Responsive**: Accessible across all devices

## 📁 Project Structure

```
mwecau_election_platform/
├── docs/
│   └── MWECAU-Voting-Guide.md          # User guide and documentation
├── src/
│   ├── backend/                        # Backend API implementation
│   │   └── README.md                   # Backend-specific documentation
│   ├── frontend/                       # Frontend web application
│   │   └── README.md                   # Frontend-specific documentation
│   └── full_stack/                     # Integrated full-stack application
│       ├── core/                       # Core Django application
│       ├── election/                   # Election-specific functionality
│       ├── manage.py                   # Django management script
│       ├── mw_es/                      # Project settings and configuration
│       ├── venv/                       # Python virtual environment
│       └── README.md                   # Full-stack specific documentation
├── path.txt                            # Project path documentation
└── README.md                           # This file
```

### Module Documentation

Each codebase section has detailed documentation:

- **[Backend Documentation](src/backend/README.md)** - REST API, database models, and server configuration
- **[Frontend Documentation](src/frontend/README.md)** - UI components, styling, and client-side functionality
- **[Full-stack Documentation](src/full_stack/README.md)** - Integrated application setup and deployment

## 🛠 Technology Stack

### Backend
- **Framework**: Django (Python)
- **Database**: MySQL/PostgreSQL/SQLite (configurable)
- **API**: Django REST Framework
- **Authentication**: Django Authentication System

### Frontend
- **Languages**: HTML5, CSS3, JavaScript (ES6+)
- **Styling**: CSS3 with modern responsive design
- **Interactivity**: Vanilla JavaScript

### Development Tools
- **Version Control**: Git
- **Package Management**: pip (Python), npm (optional for build tools)
- **Environment**: Python Virtual Environment

## 🚀 Getting Started

### Prerequisites

- Python 3.8+ installed
- Git installed
- Database system (MySQL/PostgreSQL) or SQLite for development

### Quick Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/mwecau-ict-club/mwecau_election_platform.git
   cd mwecau_election_platform
   ```

2. **Choose your development approach**:
   - **Full-stack Development**: Navigate to `src/full_stack/` and follow the [Full-stack README](src/full_stack/README.md)
   - **Separate Backend/Frontend**: Follow individual README files in `src/backend/` and `src/frontend/`

3. **Read the documentation**
   - Check `docs/MWECAU-Voting-Guide.md` for user guidelines
   - Review module-specific README files for detailed setup instructions

## 💻 Development Setup

### For Full-stack Development

```bash
cd src/full_stack/
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### For Separate Development

1. **Backend Setup**:
   ```bash
   cd src/backend/
   # Follow backend/README.md instructions
   ```

2. **Frontend Setup**:
   ```bash
   cd src/frontend/
   # Follow frontend/README.md instructions
   ```

## 🤝 Contributing

We welcome contributions from the MWECAU community and beyond! Here's how you can contribute:

### Getting Started with Contributions

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Create a feature branch** from `main`
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. **Make your changes** following our coding standards
5. **Test thoroughly** before submitting
6. **Commit with clear messages**
   ```bash
   git commit -m "Add: Brief description of your changes"
   ```
7. **Push to your fork** and create a Pull Request

### Contribution Guidelines

#### Code Standards
- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add comments for complex logic
- Write docstrings for functions and classes

#### Database Changes
- Always create migrations for model changes
- Test migrations on sample data
- Document any breaking changes

#### Frontend Standards
- Use semantic HTML5
- Follow CSS naming conventions
- Ensure mobile responsiveness
- Test across different browsers

#### Testing
- Write unit tests for new functionality
- Ensure all existing tests pass
- Test user workflows end-to-end

### Types of Contributions

- **🐛 Bug Reports**: Report issues with detailed reproduction steps
- **✨ Feature Requests**: Suggest new features with clear use cases
- **📝 Documentation**: Improve README files, add code comments
- **🔧 Bug Fixes**: Fix reported issues
- **🚀 New Features**: Implement requested or approved features
- **🎨 UI/UX Improvements**: Enhance user interface and experience

### Review Process

All contributions go through:
1. **Code Review** by project maintainers
2. **Testing** in development environment
3. **Integration** testing with existing features
4. **Documentation** updates if needed

## 📚 Documentation

- **[User Guide](docs/MWECAU-Voting-Guide.md)** - How to use the voting platform
- **[Backend API](src/backend/README.md)** - API endpoints and database schema
- **[Frontend Guide](src/frontend/README.md)** - UI components and styling
- **[Full-stack Setup](src/full_stack/README.md)** - Complete application deployment

## 📞 Contact

### Primary Contact
- **Email**: mwecauictclub@gmail.com
- **Organization**: MWECAU ICT Club

### Project Management
For project-specific inquiries, technical questions, or collaboration opportunities, please contact the project manager through the main email address above.

### Support Channels
- **Issues**: Use GitHub Issues for bug reports and feature requests
- **Discussions**: Use GitHub Discussions for general questions
- **Email**: Direct technical support via mwecauictclub@gmail.com

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 MWECAU ICT Club

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 🙏 Acknowledgments

- **MWECAU ICT Club** - Project initiation and ongoing support
- **Mwenge Catholic University** - Institutional support
- **Contributors** - All developers who have contributed to this project
- **Community** - Students and staff who provide feedback and testing

---

**Repository URL**: https://github.com/mwecau-ict-club/mwecau_election_platform.git

For the latest updates and releases, please visit our GitHub repository.