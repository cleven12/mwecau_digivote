from django.core.management.base import BaseCommand
from core.models import Course, CollegeData
import csv
import io

class Command(BaseCommand):
    help = 'Imports college data from CSV'

    def handle(self, *args, **kwargs):
        # Add the CSV data directly
        csv_data = """registration_number, full_name, course_code, course_name
T/DEG/2020/0001, Paul Mbise, BsChem, Bachelor of Science in Chemistry
T/DEG/2020/0002, Neema Mwijage, BsCS, Bachelor of Science in Computer Science
T/DEG/2020/0003, George Mkenda, BsMathStat, Bachelor of Science in Mathematics and Statistics
T/DEG/2020/0004, Victor Ndege, BsEd, Bachelor Science with Education
T/DEG/2020/0005, Francis Mtitu, BsBio, Bachelor of Science in Applied Biology
T/DEG/2020/0006, Anyes Mushi, BAccFin, Bachelor of Accounting and Finance
T/DEG/2020/0007, Laureen Sanga, BProcSCM, Bachelor of Procurement and Supply Chain Management
T/DEG/2020/0008, Jesca Nyanda, BAProjMgmt, Bachelor of Arts in Project Planning and Management
T/DEG/2020/0009, Faustine Mwita, BABusAdmin, Bachelor of Arts in Business Administration Management
T/DEG/2020/0010, Cleven Komba, BASW-HR, Bachelor of Arts in Social Work and Human Rights
T/DEG/2020/0011, Anna Mwaya, LLB, Bachelor of Laws
T/DEG/2020/0012, Evenlight Kabwe, BASocSW, Bachelor of Arts in Sociology and Social Work
T/DEG/2020/0013, Glory Nguma, BAGeoEnv, Bachelor of Arts in Geography and Environmental Studies
T/DEG/2020/0014, Nehemia Bakari, BAEd, Bachelor of Arts with Education
T/DEG/2020/0015, Nyanda Nkwabi, BsChem, Bachelor of Science in Chemistry
T/DEG/2020/0016, Massawe Mwandu, BsCS, Bachelor of Science in Computer Science
T/DEG/2020/0017, Debora Mbezi, BsMathStat, Bachelor of Science in Mathematics and Statistics
T/DEG/2020/0018, Obeni Chitende, BsEd, Bachelor Science with Education
T/DEG/2020/0019, Jackson Nguvumali, BsBio, Bachelor of Science in Applied Biology
T/DEG/2020/0020, Levina Mwingira, BAccFin, Bachelor of Accounting and Finance
T/DEG/2020/0021, Loveness Mdoe, BProcSCM, Bachelor of Procurement and Supply Chain Management
T/DEG/2020/0022, Benson Samia, BAProjMgmt, Bachelor of Arts in Project Planning and Management
T/DEG/2020/0023, Samia Othman, BABusAdmin, Bachelor of Arts in Business Administration Management
T/DEG/2020/0024, Cleophas Mrema, BASW-HR, Bachelor of Arts in Social Work and Human Rights
T/DEG/2020/0025, Esther Mwakatobe, LLB, Bachelor of Laws
T/DEG/2020/0026, Gloria Mwinuka, BASocSW, Bachelor of Arts in Sociology and Social Work
T/DEG/2020/0027, Nyota Mwita, BAGeoEnv, Bachelor of Arts in Geography and Environmental Studies
T/DEG/2020/0028, Neema Abas, BAEd, Bachelor of Arts with Education
T/DEG/2020/0029, Victor Ndago, BsChem, Bachelor of Science in Chemistry
T/DEG/2020/0030, George Mwinyi, BsCS, Bachelor of Science in Computer Science
T/DEG/2020/0031, Francesca Kisasi, BsMathStat, Bachelor of Science in Mathematics and Statistics
T/DEG/2020/0032, Faustine Kahangwa, BsEd, Bachelor Science with Education
T/DEG/2020/0033, Cleophas Kitundu, BsBio, Bachelor of Science in Applied Biology
T/DEG/2020/0034, Laureen Mtibwa, BAccFin, Bachelor of Accounting and Finance
T/DEG/2020/0035, Anyes Rija, BProcSCM, Bachelor of Procurement and Supply Chain Management
T/DEG/2020/0036, Jackson Maduhu, BAProjMgmt, Bachelor of Arts in Project Planning and Management
T/DEG/2020/0037, Deborah Majaliwa, BABusAdmin, Bachelor of Arts in Business Administration Management
T/DEG/2020/0038, Nyanda Seba, BASW-HR, Bachelor of Arts in Social Work and Human Rights
T/DEG/2020/0039, Benson Kamugisha, LLB, Bachelor of Laws
T/DEG/2020/0040, Faustin Kipande, BASocSW, Bachelor of Arts in Sociology and Social Work
T/DEG/2020/0041, Gloria Nyara, BAGeoEnv, Bachelor of Arts in Geography and Environmental Studies
T/DEG/2020/0042, Nehemia Kipanya, BAEd, Bachelor of Arts with Education
T/DEG/2020/0043, Deborah Lubuva, BsChem, Bachelor of Science in Chemistry
T/DEG/2020/0044, Evenlight Temba, BsCS, Bachelor of Science in Computer Science
T/DEG/2020/0045, Nyanda Matata, BsMathStat, Bachelor of Science in Mathematics and Statistics
T/DEG/2020/0046, Obeni Ndumbalo, BsEd, Bachelor Science with Education
T/DEG/2020/0047, Anna Lihamba, BsBio, Bachelor of Science in Applied Biology
T/DEG/2020/0048, Cleven Mutaka, BAccFin, Bachelor of Accounting and Finance
T/DEG/2020/0049, Loveness Mandefu, BProcSCM, Bachelor of Procurement and Supply Chain Management
T/DEG/2020/0050, George Kiponda, BAProjMgmt, Bachelor of Arts in Project Planning and Management
T/DEG/2020/0051, Lucia Mbwana, BABusAdmin, Bachelor of Arts in Business Administration Management
T/DEG/2020/0052, Benson Ndori, BASW-HR, Bachelor of Arts in Social Work and Human Rights
T/DEG/2020/0053, Neema Kongoro, LLB, Bachelor of Laws
T/DEG/2020/0054, Victor Mnyasa, BASocSW, Bachelor of Arts in Sociology and Social Work
T/DEG/2020/0055, Laureen Mwinuka, BAGeoEnv, Bachelor of Arts in Geography and Environmental Studies
T/DEG/2020/0056, Nyota Mishi, BAEd, Bachelor of Arts with Education
T/DEG/2020/0057, George Musoke, BsChem, Bachelor of Science in Chemistry
T/DEG/2020/0058, Faustine Mahiri, BsCS, Bachelor of Science in Computer Science
T/DEG/2020/0059, Debora Ndela, BsMathStat, Bachelor of Science in Mathematics and Statistics
T/DEG/2020/0060, Loveness Msuya, BsEd, Bachelor Science with Education
T/DEG/2020/0061, Victor Mponda, BsBio, Bachelor of Science in Applied Biology
T/DEG/2020/0062, Jackson Mchoro, BAccFin, Bachelor of Accounting and Finance
T/DEG/2020/0063, Benson Ramadhani, BProcSCM, Bachelor of Procurement and Supply Chain Management
T/DEG/2020/0064, Cleven Munuo, BAProjMgmt, Bachelor of Arts in Project Planning and Management
T/DEG/2020/0065, Evenlight Samweli, BABusAdmin, Bachelor of Arts in Business Administration Management
T/DEG/2020/0066, Nyanda Kashindi, BASW-HR, Bachelor of Arts in Social Work and Human Rights
T/DEG/2020/0067, Nehemia Ndunguru, LLB, Bachelor of Laws
T/DEG/2020/0068, Faustine Kubwa, BASocSW, Bachelor of Arts in Sociology and Social Work
T/DEG/2020/0069, George Mwanjisi, BAGeoEnv, Bachelor of Arts in Geography and Environmental Studies
T/DEG/2020/0070, Anna Kitima, BAEd, Bachelor of Arts with Education
T/DEG/2020/0071, Cleven Kihangwa, BsChem, Bachelor of Science in Chemistry
T/DEG/2020/0072, Laureen Kaligula, BsCS, Bachelor of Science in Computer Science
T/DEG/2020/0073, Victor Kayombo, BsMathStat, Bachelor of Science in Mathematics and Statistics
T/DEG/2020/0074, Anyes Kipuka, BsEd, Bachelor Science with Education
T/DEG/2020/0075, Jackson Nguvumali, BsBio, Bachelor of Science in Applied Biology
T/DEG/2020/0076, Gloria Luhanga, BAccFin, Bachelor of Accounting and Finance
T/DEG/2020/0077, Levina Chabuga, BProcSCM, Bachelor of Procurement and Supply Chain Management
T/DEG/2020/0078, Neema Liundi, BAProjMgmt, Bachelor of Arts in Project Planning and Management
T/DEG/2020/0079, Nyota Khamisi, BABusAdmin, Bachelor of Arts in Business Administration Management
T/DEG/2020/0080, Francis Tuma, BASW-HR, Bachelor of Arts in Social Work and Human Rights
T/DEG/2020/0081, Anyes Kalembwa, LLB, Bachelor of Laws
T/DEG/2020/0082, Cleven Mwakalindile, BASocSW, Bachelor of Arts in Sociology and Social Work
T/DEG/2020/0083, Laureen Kipunde, BAGeoEnv, Bachelor of Arts in Geography and Environmental Studies
T/DEG/2020/0084, Nyanda Mkandawile, BAEd, Bachelor of Arts with Education
T/DEG/2020/0085, Faustine Kachoka, BsChem, Bachelor of Science in Chemistry
T/DEG/2020/0086, Benson Ngamba, BsCS, Bachelor of Science in Computer Science
T/DEG/2020/0087, Gloria Muhumbo, BsMathStat, Bachelor of Science in Mathematics and Statistics
T/DEG/2020/0088, Debora Chirwa, BsEd, Bachelor Science with Education
T/DEG/2020/0089, Anna Lutabingwa, BsBio, Bachelor of Science in Applied Biology
T/DEG/2020/0090, Cleven Malemba, BAccFin, Bachelor of Accounting and Finance
T/DEG/2020/0091, Neema Pembe, BProcSCM, Bachelor of Procurement and Supply Chain Management
T/DEG/2020/0092, Faustine Kabambi, BAProjMgmt, Bachelor of Arts in Project Planning and Management
T/DEG/2020/0093, Anyes Mwaka, BABusAdmin, Bachelor of Arts in Business Administration Management
T/DEG/2020/0094, Jackson Kibona, BASW-HR, Bachelor of Arts in Social Work and Human Rights
T/DEG/2020/0095, Victor Juma, LLB, Bachelor of Laws
T/DEG/2020/0096, Loveness Kijazi, BASocSW, Bachelor of Arts in Sociology and Social Work
T/DEG/2020/0097, Benson Kiponda, BAGeoEnv, Bachelor of Arts in Geography and Environmental Studies
T/DEG/2020/0098, Anna Kimweri, BAEd, Bachelor of Arts with Education
T/DEG/2020/0099, Cleven Makoti, BsChem, Bachelor of Science in Chemistry
T/DEG/2020/0100, Laureen Lyimo, BsCS, Bachelor of Science in Computer Science"""

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