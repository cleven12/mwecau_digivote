# Contributing to MWECAU Digital Voting System (Club Edition)

Thank you for contributing to this club project! This is a lightweight Django voting system using plain HTML/CSS (no Bootstrap) to encourage community contributions.

## Getting Started

**Prerequisites:**
- Python 3.8+
- Basic Django knowledge
- HTML/CSS skills (no framework required)

**Setup:**
```bash
git clone https://github.com/mwecauictclub/mwecau_election_platform.git
cd mwecau_election_platform
cp .env.example .env  # Edit with your settings
cd src
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r ../requirements.txt
python manage.py migrate
python manage.py runserver
```

## Project Structure

- `src/core/` - User management, authentication, dashboards
- `src/election/` - Election logic, voting, results
- `src/templates/` - Plain HTML templates (no Bootstrap!)
- `src/static/css/` - Custom CSS only
- `docs/` - Architecture and API documentation

## Contributing Guidelines

### UI & Frontend
- **Plain HTML/CSS only** - No Bootstrap, no complex frameworks
- Keep styles simple and readable
- Use semantic HTML elements
- Add your own CSS creativity while maintaining usability
- Font Awesome icons are okay (already included)

### Backend Code
- Follow Django best practices
- Use Django ORM appropriately
- Write clear docstrings for new functions
- Keep views focused and testable
- Follow PEP 8 style guidelines

### Database Changes
- Include migration files with your PRs
- Test migrations on fresh database
- Document any manual data setup needed
- Consider backward compatibility

### Testing
Since this is a club project:
- Test your changes manually before submitting
- Verify login/registration flows work
- Test voting and results if you modify election logic
- Check responsive design on mobile/desktop

### Branch Strategy
- Fork the repository or create feature branches
- Work from `final-delivery` branch
- Make focused commits with clear messages
- One feature per pull request

## Adding New Features

### Common Contributions Welcome:
1. **UI Improvements** - Better styling, responsive design, accessibility
2. **New Dashboard Widgets** - Analytics, charts, statistics
3. **Email Templates** - Better notification designs
4. **API Enhancements** - New endpoints, better serialization
5. **Security Improvements** - Rate limiting, validation
6. **Documentation** - Setup guides, API docs, tutorials

### Before You Start:
1. Open an issue describing your planned changes
2. Get feedback from maintainers
3. Check if someone else is already working on it
4. Keep the scope small and manageable

## Code Style

### Python
```python
# Good: Clear, documented function
def calculate_election_results(election_id):
    """
    Calculate and return voting results for an election.
    
    Args:
        election_id: ID of the election
        
    Returns:
        dict: Results with candidate vote counts
    """
    election = Election.objects.get(id=election_id)
    # implementation...
```

### Templates (HTML/CSS)
```html
<!-- Good: Semantic HTML, simple styling -->
<section class="election-results">
    <h2>Election Results</h2>
    <div class="candidate-list">
        <div class="candidate-card">
            <h3>{{ candidate.name }}</h3>
            <p class="vote-count">{{ candidate.vote_count }} votes</p>
        </div>
    </div>
</section>
```

### CSS
```css
/* Good: Simple, readable styles */
.candidate-card {
    padding: 1rem;
    margin: 0.5rem 0;
    border: 1px solid #ddd;
    border-radius: 4px;
    background: white;
}

.candidate-card:hover {
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
```

## Security Guidelines

- Never commit secrets, API keys, or passwords
- Use environment variables for configuration
- Validate all user inputs
- Follow Django security best practices
- Report security issues privately to maintainers

## Pull Request Process

### Before Submitting:
1. Test your changes locally
2. Update documentation if needed
3. Add yourself to the contributors list (see Acknowledgments below)
4. Write a clear PR description

### PR Template:
```
## What does this PR do?
Brief description of the changes

## Why is this change needed?
Problem being solved or feature being added

## How to test:
Steps to verify the changes work

## Screenshots (if UI changes):
Before/after images

## Checklist:
- [ ] Tested locally
- [ ] No secrets committed
- [ ] Documentation updated
- [ ] Added myself to contributors
```

## Acknowledgments

This project is maintained by the MWECAU ICT Club with contributions from:

- **@cleven12** (Cleven) - Original developer and maintainer
- **@Lajokjohn** (Lajokjohn) - Contributor
- **@FaustineEmmanuel** (Faustine) - Contributor
- **@mwecauictclub** (Mwecau_ict_club) - Club coordination

### Adding Yourself:
When you contribute, add your GitHub username to the list above in your PR!

## Getting Help

- **Issues:** [Open a GitHub issue](https://github.com/mwecauictclub/mwecau_election_platform/issues) for bugs or feature requests
- **Questions:** Comment on existing issues or open a discussion
- **Chat:** Contact @mwecauictclub for club-related questions
- **Original Development:** [cleven12/university_elec_api](https://github.com/cleven12/university_elec_api) for development history

## Club Development Philosophy

This project emphasizes:
- **Learning opportunities** for club members
- **Simple, maintainable code** over complex solutions
- **Community collaboration** and knowledge sharing
- **Practical skills** in web development and Django

Your contributions help fellow students learn and improve the platform!

## License & Usage

This is an educational project for MWECAU students. Feel free to:
- Use it for learning Django development
- Fork it for your own school projects
- Adapt it for other voting/election needs
- Contribute improvements back to the community

Thank you for contributing to our club project! 🚀
