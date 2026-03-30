from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from base.models import (
    Company, CompanyStaff, Position, Candidate, CandidateInterest,
    Note, Submission, Question, QuestionChoice, Answer, AnswerChoice, ApplicationToken
)
from django.utils import timezone
import uuid

class Command(BaseCommand):
    help = 'Create sample data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample data...')

        #Users
        admin = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        staff1 = User.objects.create_user('staff1', 'staff1@example.com', 'pass123', is_staff=True)
        staff2 = User.objects.create_user('staff2', 'staff2@example.com', 'pass123', is_staff=True)
        staff3 = User.objects.create_user('staff3', 'staff3@example.com', 'pass123', is_staff=True)

        #Companies
        company1 = Company.objects.create(slug='company1', title='Company1', description='Company1 description', is_active=True)
        company2 = Company.objects.create(slug='company2', title='Company2', description='Company2 description', is_active=True)
        company3 = Company.objects.create(slug='company3', title='Company3', description='Company3 description', is_active=True)
        company4 = Company.objects.create(slug='company4', title='Company4', description='Company4 description', is_active=True)
        company5 = Company.objects.create(slug='company5', title='Company5', description='Company5 description', is_active=True)
        company6 = Company.objects.create(slug='company6', title='Company6', description='Company6 description', is_active=True)

        #CompanyStaff
        CompanyStaff.objects.create(user=staff1, company=company1, is_admin=True)
        CompanyStaff.objects.create(user=staff2, company=company1, is_admin=False)
        CompanyStaff.objects.create(user=staff1, company=company2, is_admin=True)
        CompanyStaff.objects.create(user=staff3, company=company3, is_admin=False)
        CompanyStaff.objects.create(user=staff2, company=company4, is_admin=True)
        CompanyStaff.objects.create(user=staff3, company=company5, is_admin=False)

        #Positions
        position1 = Position.objects.create(company=company1, title='Position1', description='Position1 desc', employment_type='full_time', is_active=True)
        position2 = Position.objects.create(company=company1, title='Position2', description='Position2 desc', employment_type='full_time')
        position3 = Position.objects.create(company=company2, title='Position3', description='Position3 desc', employment_type='contract')
        position4 = Position.objects.create(company=company3, title='Position4', description='Position4 desc', employment_type='full_time')
        Position.objects.create(company=company1, title='Position5', employment_type='full_time')
        Position.objects.create(company=company2, title='Position6', employment_type='part_time')
        Position.objects.create(company=company3, title='Position7', employment_type='internship')
        Position.objects.create(company=company4, title='Position8', employment_type='full_time')

        #Candidates
        candidate1 = Candidate.objects.create(email='candidate1@example.com', first_name='Candidate1', last_name='Last1', phone='555-0001')
        candidate2 = Candidate.objects.create(email='candidate2@example.com', first_name='Candidate2', last_name='Last2', phone='555-0002')
        candidate3 = Candidate.objects.create(email='candidate3@example.com', first_name='Candidate3', last_name='Last3', phone='555-0003')
        candidate4 = Candidate.objects.create(email='candidate4@example.com', first_name='Candidate4', last_name='Last4', phone='555-0004')
        candidate5 = Candidate.objects.create(email='candidate5@example.com', first_name='Candidate5', last_name='Last5')
        candidate6 = Candidate.objects.create(email='candidate6@example.com', first_name='Candidate6', last_name='Last6')

        #CandidateInterest
        CandidateInterest.objects.create(candidate=candidate1, label='Interest1', strength_1_to_10=9)
        CandidateInterest.objects.create(candidate=candidate1, label='Interest2', strength_1_to_10=8)
        CandidateInterest.objects.create(candidate=candidate2, label='Interest3', strength_1_to_10=10)
        CandidateInterest.objects.create(candidate=candidate2, label='Interest4', strength_1_to_10=7)
        CandidateInterest.objects.create(candidate=candidate3, label='Interest5', strength_1_to_10=6)
        CandidateInterest.objects.create(candidate=candidate4, label='Interest6', strength_1_to_10=9)
        CandidateInterest.objects.create(candidate=candidate5, label='Interest7', strength_1_to_10=8)
        CandidateInterest.objects.create(candidate=candidate6, label='Interest8', strength_1_to_10=10)
        CandidateInterest.objects.create(candidate=candidate1, label='Interest9', strength_1_to_10=5)
        CandidateInterest.objects.create(candidate=candidate2, label='Interest10', strength_1_to_10=7)

        #Notes
        Note.objects.create(candidate=candidate1, author=staff1, body='Note1')
        Note.objects.create(candidate=candidate2, author=staff2, body='Note2')
        Note.objects.create(candidate=candidate3, author=staff1, body='Note3')
        Note.objects.create(candidate=candidate4, author=staff3, body='Note4')
        Note.objects.create(candidate=candidate5, author=staff2, body='Note5')
        Note.objects.create(candidate=candidate6, author=staff1, body='Note6')

        #ApplicationToken
        ApplicationToken.objects.create(candidate=candidate1, token=uuid.uuid4())
        ApplicationToken.objects.create(candidate=candidate2, token=uuid.uuid4())
        ApplicationToken.objects.create(candidate=candidate3, token=uuid.uuid4())
        ApplicationToken.objects.create(candidate=candidate4, token=uuid.uuid4())
        ApplicationToken.objects.create(candidate=candidate5, token=uuid.uuid4())

        #Submissions
        sub1 = Submission.objects.create(candidate=candidate1, position=position1, payload={'data': 1}, status='finished', finished_at=timezone.now())
        sub2 = Submission.objects.create(candidate=candidate2, position=position2, status='new')
        sub3 = Submission.objects.create(candidate=candidate3, position=position3, status='finished')
        sub4 = Submission.objects.create(candidate=candidate4, position=position4, status='finished')
        Submission.objects.create(candidate=candidate5, position=position1, status='new')
        Submission.objects.create(candidate=candidate6, position=position2, status='finished')
        Submission.objects.create(candidate=candidate1, position=position3, status='finished')
        Submission.objects.create(candidate=candidate2, position=position4, status='new')

        #Questions
        q1 = Question.objects.create(position=position1, prompt='Question1', question_type='rating', is_required=True, sort_order=1, page=2)
        q2 = Question.objects.create(position=position1, prompt='Question2', question_type='text', is_required=True, sort_order=2)
        q3 = Question.objects.create(position=position2, prompt='Question3', question_type='yesno', is_required=True)
        Question.objects.create(position=position2, prompt='Question4', question_type='rating', is_required=True, sort_order=3, page=2)
        Question.objects.create(position=position3, prompt='Question5', question_type='text', is_required=True, sort_order=1)
        Question.objects.create(position=position3, prompt='Question6', question_type='yesno', is_required=True)
        Question.objects.create(position=position4, prompt='Question7', question_type='rating', is_required=True, sort_order=2)
        Question.objects.create(position=position4, prompt='Question8', question_type='text', is_required=True)

        #QuestionChoice
        qc1 = QuestionChoice.objects.create(question=q1, label='Choice1', value='choice1', sort_order=1)

        #Answers
        Answer.objects.create(submission=sub1, question=q1, int_value=9)
        Answer.objects.create(submission=sub1, question=q2, text_value='Answer text 1')
        Answer.objects.create(submission=sub3, question=q1, int_value=7)
        Answer.objects.create(submission=sub4, question=q3, bool_value=True)
        Answer.objects.create(submission=sub2, question=q2, text_value='Answer text 2')
        Answer.objects.create(submission=sub1, question=q3, bool_value=False)
        Answer.objects.create(submission=sub3, question=q1, int_value=8)
        Answer.objects.create(submission=sub4, question=q2, text_value='Answer text 3')

        #AnswerChoice
        AnswerChoice.objects.create(answer=Answer.objects.first(), choice=qc1)

        self.stdout.write('Sample data created')