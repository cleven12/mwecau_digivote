from django.core.management.base import BaseCommand
from core.models import Course, CollegeData
import csv
import io

class Command(BaseCommand):
    help = 'Imports college data from CSV'

    def handle(self, *args, **kwargs):
        # Add the CSV data directly
        csv_data = """registration_number, full_name, course_code, course_name
REG-001, Paul Mbise, BsChem, Bachelor of Science in Chemistry
REG-002, Neema Mwijage, BsCS, Bachelor of Science in Computer Science
REG-003, George Mkenda, BsMathStat, Bachelor of Science in Mathematics and Statistics
REG-004, Victor Ndege, BsEd, Bachelor Science with Education
REG-005, Francis Mtitu, BsBio, Bachelor of Science in Applied Biology
REG-006, Anyes Mushi, BAccFin, Bachelor of Accounting and Finance
REG-007, Laureen Sanga, BProcSCM, Bachelor of Procurement and Supply Chain Management
REG-008, Jesca Nyanda, BAProjMgmt, Bachelor of Arts in Project Planning and Management
REG-009, Faustine Mwita, BABusAdmin, Bachelor of Arts in Business Administration Management
REG-010, Cleven Komba, BASW-HR, Bachelor of Arts in Social Work and Human Rights
REG-011, Anna Mwaya, LLB, Bachelor of Laws
REG-012, Evenlight Kabwe, BASocSW, Bachelor of Arts in Sociology and Social Work
REG-013, Glory Nguma, BAGeoEnv, Bachelor of Arts in Geography and Environmental Studies
REG-014, Nehemia Bakari, BAEd, Bachelor of Arts with Education
REG-015, Nyanda Nkwabi, BsChem, Bachelor of Science in Chemistry
REG-016, Massawe Mwandu, BsCS, Bachelor of Science in Computer Science
REG-017, Debora Mbezi, BsMathStat, Bachelor of Science in Mathematics and Statistics
REG-018, Obeni Chitende, BsEd, Bachelor Science with Education
REG-019, Jackson Nguvumali, BsBio, Bachelor of Science in Applied Biology
REG-020, Levina Mwingira, BAccFin, Bachelor of Accounting and Finance
REG-021, Loveness Mdoe, BProcSCM, Bachelor of Procurement and Supply Chain Management
REG-022, Benson Samia, BAProjMgmt, Bachelor of Arts in Project Planning and Management
REG-023, Samia Othman, BABusAdmin, Bachelor of Arts in Business Administration Management
REG-024, Cleophas Mrema, BASW-HR, Bachelor of Arts in Social Work and Human Rights
REG-025, Esther Mwakatobe, LLB, Bachelor of Laws
REG-026, Gloria Mwinuka, BASocSW, Bachelor of Arts in Sociology and Social Work
REG-027, Nyota Mwita, BAGeoEnv, Bachelor of Arts in Geography and Environmental Studies
REG-028, Neema Abas, BAEd, Bachelor of Arts with Education
REG-029, Victor Ndago, BsChem, Bachelor of Science in Chemistry
REG-030, George Mwinyi, BsCS, Bachelor of Science in Computer Science
REG-031, Francesca Kisasi, BsMathStat, Bachelor of Science in Mathematics and Statistics
REG-032, Faustine Kahangwa, BsEd, Bachelor Science with Education
REG-033, Cleophas Kitundu, BsBio, Bachelor of Science in Applied Biology
REG-034, Laureen Mtibwa, BAccFin, Bachelor of Accounting and Finance
REG-035, Anyes Rija, BProcSCM, Bachelor of Procurement and Supply Chain Management
REG-036, Jackson Maduhu, BAProjMgmt, Bachelor of Arts in Project Planning and Management
REG-037, Deborah Majaliwa, BABusAdmin, Bachelor of Arts in Business Administration Management
REG-038, Nyanda Seba, BASW-HR, Bachelor of Arts in Social Work and Human Rights
REG-039, Benson Kamugisha, LLB, Bachelor of Laws
REG-040, Faustin Kipande, BASocSW, Bachelor of Arts in Sociology and Social Work
REG-041, Gloria Nyara, BAGeoEnv, Bachelor of Arts in Geography and Environmental Studies
REG-042, Nehemia Kipanya, BAEd, Bachelor of Arts with Education
REG-043, Deborah Lubuva, BsChem, Bachelor of Science in Chemistry
REG-044, Evenlight Temba, BsCS, Bachelor of Science in Computer Science
REG-045, Nyanda Matata, BsMathStat, Bachelor of Science in Mathematics and Statistics
REG-046, Obeni Ndumbalo, BsEd, Bachelor Science with Education
REG-047, Anna Lihamba, BsBio, Bachelor of Science in Applied Biology
REG-048, Cleven Mutaka, BAccFin, Bachelor of Accounting and Finance
REG-049, Loveness Mandefu, BProcSCM, Bachelor of Procurement and Supply Chain Management
REG-050, George Kiponda, BAProjMgmt, Bachelor of Arts in Project Planning and Management
REG-051, Lucia Mbwana, BABusAdmin, Bachelor of Arts in Business Administration Management
REG-052, Benson Ndori, BASW-HR, Bachelor of Arts in Social Work and Human Rights
REG-053, Neema Kongoro, LLB, Bachelor of Laws
REG-054, Victor Mnyasa, BASocSW, Bachelor of Arts in Sociology and Social Work
REG-055, Laureen Mwinuka, BAGeoEnv, Bachelor of Arts in Geography and Environmental Studies
REG-056, Nyota Mishi, BAEd, Bachelor of Arts with Education
REG-057, George Musoke, BsChem, Bachelor of Science in Chemistry
REG-058, Faustine Mahiri, BsCS, Bachelor of Science in Computer Science
REG-059, Debora Ndela, BsMathStat, Bachelor of Science in Mathematics and Statistics
REG-060, Loveness Msuya, BsEd, Bachelor Science with Education
REG-061, Victor Mponda, BsBio, Bachelor of Science in Applied Biology
REG-062, Jackson Mchoro, BAccFin, Bachelor of Accounting and Finance
REG-063, Benson Ramadhani, BProcSCM, Bachelor of Procurement and Supply Chain Management
REG-064, Cleven Munuo, BAProjMgmt, Bachelor of Arts in Project Planning and Management
REG-065, Evenlight Samweli, BABusAdmin, Bachelor of Arts in Business Administration Management
REG-066, Nyanda Kashindi, BASW-HR, Bachelor of Arts in Social Work and Human Rights
REG-067, Nehemia Ndunguru, LLB, Bachelor of Laws
REG-068, Faustine Kubwa, BASocSW, Bachelor of Arts in Sociology and Social Work
REG-069, George Mwanjisi, BAGeoEnv, Bachelor of Arts in Geography and Environmental Studies
REG-070, Anna Kitima, BAEd, Bachelor of Arts with Education
REG-071, Cleven Kihangwa, BsChem, Bachelor of Science in Chemistry
REG-072, Laureen Kaligula, BsCS, Bachelor of Science in Computer Science
REG-073, Victor Kayombo, BsMathStat, Bachelor of Science in Mathematics and Statistics
REG-074, Anyes Kipuka, BsEd, Bachelor Science with Education
REG-075, Jackson Nguvumali, BsBio, Bachelor of Science in Applied Biology
REG-076, Gloria Luhanga, BAccFin, Bachelor of Accounting and Finance
REG-077, Levina Chabuga, BProcSCM, Bachelor of Procurement and Supply Chain Management
REG-078, Neema Liundi, BAProjMgmt, Bachelor of Arts in Project Planning and Management
REG-079, Nyota Khamisi, BABusAdmin, Bachelor of Arts in Business Administration Management
REG-080, Francis Tuma, BASW-HR, Bachelor of Arts in Social Work and Human Rights
REG-081, Anyes Kalembwa, LLB, Bachelor of Laws
REG-082, Cleven Mwakalindile, BASocSW, Bachelor of Arts in Sociology and Social Work
REG-083, Laureen Kipunde, BAGeoEnv, Bachelor of Arts in Geography and Environmental Studies
REG-084, Nyanda Mkandawile, BAEd, Bachelor of Arts with Education
REG-085, Faustine Kachoka, BsChem, Bachelor of Science in Chemistry
REG-086, Benson Ngamba, BsCS, Bachelor of Science in Computer Science
REG-087, Gloria Muhumbo, BsMathStat, Bachelor of Science in Mathematics and Statistics
REG-088, Debora Chirwa, BsEd, Bachelor Science with Education
REG-089, Anna Lutabingwa, BsBio, Bachelor of Science in Applied Biology
REG-090, Cleven Malemba, BAccFin, Bachelor of Accounting and Finance
REG-091, Neema Pembe, BProcSCM, Bachelor of Procurement and Supply Chain Management
REG-092, Faustine Kabambi, BAProjMgmt, Bachelor of Arts in Project Planning and Management
REG-093, Anyes Mwaka, BABusAdmin, Bachelor of Arts in Business Administration Management
REG-094, Jackson Kibona, BASW-HR, Bachelor of Arts in Social Work and Human Rights
REG-095, Victor Juma, LLB, Bachelor of Laws
REG-096, Loveness Kijazi, BASocSW, Bachelor of Arts in Sociology and Social Work
REG-097, Benson Kiponda, BAGeoEnv, Bachelor of Arts in Geography and Environmental Studies
REG-098, Anna Kimweri, BAEd, Bachelor of Arts with Education
REG-099, Cleven Makoti, BsChem, Bachelor of Science in Chemistry
REG-100, Laureen Lyimo, BsCS, Bachelor of Science in Computer Science"""

        csv_file = io.StringIO(csv_data)
        reader = csv.reader(csv_file, delimiter=',')
        next(reader)  # Skip header row

        # Clear existing courses
        Course.objects.all().delete()
        
        # Clear existing college data
        CollegeData.objects.all().delete()
        
        # Dictionary to store unique courses
        courses = {}
        
        # First pass: create courses
        csv_file.seek(0)
        next(reader)  # Skip header row again
        for row in reader:
            registration_number = row[0].strip()
            full_name = row[1].strip()
            course_code = row[2].strip()
            course_name = row[3].strip()
            
            if course_code not in courses:
                course = Course.objects.create(
                    code=course_code,
                    name=course_name
                )
                courses[course_code] = course
                self.stdout.write(f"Created course: {course_code} - {course_name}")
        
        # Second pass: create college data
        csv_file.seek(0)
        next(reader)  # Skip header row again
        count = 0
        for row in csv.reader(csv_file, delimiter=','):
            if not row or len(row) < 4:
                continue
                
            registration_number = row[0].strip()
            full_name = row[1].strip()
            course_code = row[2].strip()
            
            # Split full_name into first_name and last_name
            name_parts = full_name.split(' ', 1)
            first_name = name_parts[0] if len(name_parts) > 0 else ''
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            if course_code in courses:
                CollegeData.objects.create(
                    registration_number=registration_number,
                    first_name=first_name,
                    last_name=last_name,
                    course=courses[course_code]
                )
                count += 1
                
        self.stdout.write(self.style.SUCCESS(f'Successfully imported {count} college data entries'))