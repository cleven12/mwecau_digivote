# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in the MWECAU DigiVote, please report it responsibly:

### Reporting Process

1. **DO NOT** create a public GitHub issue for security vulnerabilities
2. Send an email to: **mwecau.ict.club@gmail.com**
3. Include detailed information about the vulnerability
4. Allow up to 48 hours for initial response

### What to Include

- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact assessment
- Suggested fix (if available)
- Your contact information

## Security Best Practices

### For Deployment

- Always use HTTPS in production
- Set `DEBUG=False` for production environments
- Configure `ALLOWED_HOSTS` properly (never use `['*']` in production)
- Use strong database passwords
- Enable security headers
- Regular security updates

### For Development

- Never commit secrets to version control
- Use `.env` files for local configuration
- Review code changes for security implications
- Test with realistic data volumes

## Security Features

### Authentication & Authorization
- JWT token-based authentication
- Role-based access control (Student, Commissioner, etc.)
- Session management with secure cookies

### Data Protection
- Anonymous voting (votes cannot be traced back to users)
- Encrypted data transmission (HTTPS/TLS)
- Input validation and sanitization
- SQL injection protection via Django ORM

### Audit & Monitoring
- Comprehensive logging system
- Election audit trails
- User activity tracking
- Error monitoring

## Known Security Considerations

### Vote Privacy
- Votes are anonymous - system design prevents vote tracing
- Audit logs track actions but not vote content
- Database schema separates voter identity from vote choices

### Access Control
- Commissioners can manage elections but cannot see individual votes
- Students can only vote in elections they're eligible for
- Time-based access control for election periods

### Data Retention
- Personal data handling follows privacy best practices
- Election data retained for institutional records
- Logs rotated according to retention policy

## Security Updates

This project follows responsible disclosure practices:
- Security patches released as soon as possible
- Critical vulnerabilities addressed within 24-48 hours
- Regular dependency updates to address CVEs

## Contact

For security-related questions or concerns:
- **Email**: mwecau.ict.club@gmail.com
- **Repository**: [mwecauictclub/mwecau_election_platform](https://github.com/mwecauictclub/mwecau_election_platform)
- **Institution**: Mwenge Catholic University (MWECAU) ICT Club