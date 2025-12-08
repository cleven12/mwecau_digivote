"""
Management command to import courses and states from CSV files for MWECAU.
Usage: python manage.py import_mwecau_data
"""
import csv
import os
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from core.models import Course, State


class Command(BaseCommand):
    help = 'Import courses and states from CSV files for MWECAU institution'

    def add_arguments(self, parser):
        parser.add_argument(
            '--courses',
            type=str,
            default='data/courses_mwecau.csv',
            help='Path to courses CSV file'
        )
        parser.add_argument(
            '--states',
            type=str,
            default='data/states_mwecau.csv',
            help='Path to states CSV file'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without saving'
        )

    def handle(self, *args, **options):
        courses_file = options['courses']
        states_file = options['states']
        dry_run = options['dry_run']

        # Verify files exist
        if not os.path.exists(courses_file):
            raise CommandError(f'Courses file not found: {courses_file}')
        if not os.path.exists(states_file):
            raise CommandError(f'States file not found: {states_file}')

        self.stdout.write(self.style.SUCCESS(f'Loading courses from: {courses_file}'))
        self.stdout.write(self.style.SUCCESS(f'Loading states from: {states_file}'))

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be saved'))

        # Import states first (as courses might reference them)
        self._import_states(states_file, dry_run)

        # Import courses
        self._import_courses(courses_file, dry_run)

    def _import_states(self, filepath, dry_run):
        """Import states from CSV file."""
        states_created = 0
        states_updated = 0

        self.stdout.write('\n' + self.style.SUCCESS('=== IMPORTING STATES ==='))

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                if not reader.fieldnames or reader.fieldnames != ['name', 'code', 'category']:
                    raise CommandError(f'Invalid CSV format. Expected columns: name, code, category')

                for row in reader:
                    name = row['name'].strip()
                    code = row['code'].strip()
                    category = row['category'].strip()

                    if not name or not code:
                        self.stdout.write(self.style.WARNING(f'Skipping empty row: {row}'))
                        continue

                    try:
                        if not dry_run:
                            state, created = State.objects.update_or_create(
                                name=name,
                                defaults={'name': name}
                            )
                            if created:
                                states_created += 1
                                self.stdout.write(f'✓ Created state: {name}')
                            else:
                                states_updated += 1
                                self.stdout.write(f'~ Updated state: {name}')
                        else:
                            exists = State.objects.filter(name=name).exists()
                            action = 'UPDATE' if exists else 'CREATE'
                            self.stdout.write(f'[{action}] {name} ({category})')
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error processing state {name}: {str(e)}'))

        except csv.Error as e:
            raise CommandError(f'CSV parsing error: {str(e)}')
        except IOError as e:
            raise CommandError(f'File read error: {str(e)}')

        self.stdout.write(self.style.SUCCESS(
            f'\nStates: {states_created} created, {states_updated} updated'
        ))

    def _import_courses(self, filepath, dry_run):
        """Import courses from CSV file."""
        courses_created = 0
        courses_updated = 0
        duplicate_codes = {}

        self.stdout.write('\n' + self.style.SUCCESS('=== IMPORTING COURSES ==='))

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                if not reader.fieldnames or reader.fieldnames != ['code', 'name', 'duration_years', 'program_type']:
                    raise CommandError(f'Invalid CSV format. Expected columns: code, name, duration_years, program_type')

                for row in reader:
                    code = row['code'].strip()
                    name = row['name'].strip()
                    duration_years = row['duration_years'].strip()
                    program_type = row['program_type'].strip()

                    if not code or not name:
                        self.stdout.write(self.style.WARNING(f'Skipping empty row: {row}'))
                        continue

                    # Check for duplicate codes
                    if code in duplicate_codes:
                        duplicate_codes[code] += 1
                    else:
                        duplicate_codes[code] = 1

                    try:
                        duration = int(duration_years)
                    except ValueError:
                        self.stdout.write(self.style.ERROR(
                            f'Invalid duration for {code}: {duration_years}'
                        ))
                        continue

                    try:
                        if not dry_run:
                            course, created = Course.objects.update_or_create(
                                code=code,
                                defaults={
                                    'name': name,
                                    'code': code
                                }
                            )
                            if created:
                                courses_created += 1
                                self.stdout.write(
                                    f'✓ Created: {code} - {name} ({program_type}, {duration} years)'
                                )
                            else:
                                courses_updated += 1
                                self.stdout.write(
                                    f'~ Updated: {code} - {name}'
                                )
                        else:
                            exists = Course.objects.filter(code=code).exists()
                            action = 'UPDATE' if exists else 'CREATE'
                            self.stdout.write(
                                f'[{action}] {code} - {name} ({program_type}, {duration} years)'
                            )
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(
                            f'Error processing course {code}: {str(e)}'
                        ))

        except csv.Error as e:
            raise CommandError(f'CSV parsing error: {str(e)}')
        except IOError as e:
            raise CommandError(f'File read error: {str(e)}')

        # Check for duplicates
        if duplicate_codes:
            duplicates = {k: v for k, v in duplicate_codes.items() if v > 1}
            if duplicates:
                self.stdout.write(self.style.WARNING(f'\nDuplicate course codes found: {duplicates}'))

        self.stdout.write(self.style.SUCCESS(
            f'\nCourses: {courses_created} created, {courses_updated} updated'
        ))


