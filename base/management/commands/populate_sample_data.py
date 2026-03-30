from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from base.models import (
    Answer, AnswerChoice, ApplicationToken, Candidate, CandidateInterest,
    Company, CompanyStaff, Note, Position, Question, QuestionChoice, Submission,
)


class Command(BaseCommand):
    help = 'Populate the database with sample data (idempotent — safe to run multiple times)'

    def handle(self, *args, **kwargs):

        # ------------------------------------------------------------------ #
        # Companies (5)
        # ------------------------------------------------------------------ #
        company_data = [
            {"slug": "acme-corp",        "title": "Acme Corp",        "location": "New York, NY"},
            {"slug": "globex",           "title": "Globex",           "location": "Springfield, IL"},
            {"slug": "initech",          "title": "Initech",          "location": "Austin, TX"},
            {"slug": "umbrella-co",      "title": "Umbrella Co",      "location": "Raccoon City, MO"},
            {"slug": "stark-industries", "title": "Stark Industries", "location": "Malibu, CA"},
        ]
        companies = []
        for d in company_data:
            c, _ = Company.objects.get_or_create(
                slug=d["slug"],
                defaults={"title": d["title"], "location": d["location"]},
            )
            companies.append(c)
        self.stdout.write("  companies ok")

        # ------------------------------------------------------------------ #
        # Staff users + CompanyStaff (5)
        # ------------------------------------------------------------------ #
        staff_data = [
            {"email": "alice.admin@example.com", "first": "Alice", "last": "Admin", "company": companies[0], "is_admin": True,  "pw": "adminpass123"},
            {"email": "bob.staff@example.com",   "first": "Bob",   "last": "Staff", "company": companies[0], "is_admin": False, "pw": "staffpass123"},
            {"email": "carol.admin@example.com", "first": "Carol", "last": "Admin", "company": companies[1], "is_admin": True,  "pw": "carolpass123"},
            {"email": "dave.staff@example.com",  "first": "Dave",  "last": "Staff", "company": companies[2], "is_admin": False, "pw": "davepass123"},
            {"email": "eve.admin@example.com",   "first": "Eve",   "last": "Admin", "company": companies[3], "is_admin": True,  "pw": "evepass123"},
        ]
        for d in staff_data:
            user, created = User.objects.get_or_create(
                username=d["email"],
                defaults={"first_name": d["first"], "last_name": d["last"], "email": d["email"]},
            )
            if created:
                user.set_password(d["pw"])
                user.save()
            CompanyStaff.objects.get_or_create(
                user=user, company=d["company"],
                defaults={"is_admin": d["is_admin"]},
            )
        self.stdout.write("  staff ok")

        # ------------------------------------------------------------------ #
        # Positions (5)
        # ------------------------------------------------------------------ #
        position_data = [
            # [0] Acme Corp
            {"company": companies[0], "title": "Backend Engineer",    "employment_type": Position.EMPLOYMENT_FULL_TIME},
            # [1] Acme Corp
            {"company": companies[0], "title": "Product Manager",     "employment_type": Position.EMPLOYMENT_FULL_TIME},
            # [2] Globex
            {"company": companies[1], "title": "Data Scientist",      "employment_type": Position.EMPLOYMENT_CONTRACT},
            # [3] Initech
            {"company": companies[2], "title": "QA Engineer",         "employment_type": Position.EMPLOYMENT_PART_TIME},
            # [4] Umbrella Co
            {"company": companies[3], "title": "Security Researcher", "employment_type": Position.EMPLOYMENT_FULL_TIME},
        ]
        positions = []
        for d in position_data:
            p, _ = Position.objects.get_or_create(
                company=d["company"], title=d["title"],
                defaults={"employment_type": d["employment_type"]},
            )
            positions.append(p)
        self.stdout.write("  positions ok")

        # ------------------------------------------------------------------ #
        # Candidates (5) — each linked to a Django User
        # ------------------------------------------------------------------ #
        cand_data = [
            {"email": "john.doe@example.com",   "first": "John",   "last": "Doe",    "phone": "555-0101", "pw": "JohnsPassword123"},
            {"email": "jane.smith@example.com", "first": "Jane",   "last": "Smith",  "phone": "555-0102", "pw": "KittenLover123"},
            {"email": "carlos.r@example.com",   "first": "Carlos", "last": "Rivera", "phone": "555-0103", "pw": "CarlosPass123"},
            {"email": "mei.l@example.com",      "first": "Mei",    "last": "Lin",    "phone": "555-0104", "pw": "MeiPass123"},
            {"email": "omar.f@example.com",     "first": "Omar",   "last": "Farooq", "phone": "555-0105", "pw": "OmarPass123"},
        ]
        candidates = []
        for d in cand_data:
            user, created = User.objects.get_or_create(
                username=d["email"],
                defaults={"first_name": d["first"], "last_name": d["last"], "email": d["email"]},
            )
            if created:
                user.set_password(d["pw"])
                user.save()
            cand, _ = Candidate.objects.get_or_create(
                user=user,
                defaults={
                    "email":      d["email"],
                    "first_name": d["first"],
                    "last_name":  d["last"],
                    "phone":      d["phone"],
                },
            )
            candidates.append(cand)
        self.stdout.write("  candidates ok")

        # ------------------------------------------------------------------ #
        # CandidateInterest (5)
        # ------------------------------------------------------------------ #
        interest_data = [
            {"candidate": candidates[0], "label": "Python",           "strength": 9},
            {"candidate": candidates[1], "label": "Marketing",        "strength": 8},
            {"candidate": candidates[2], "label": "Machine Learning", "strength": 10},
            {"candidate": candidates[3], "label": "DevOps",           "strength": 7},
            {"candidate": candidates[4], "label": "Cybersecurity",    "strength": 9},
        ]
        for d in interest_data:
            CandidateInterest.objects.get_or_create(
                candidate=d["candidate"], label=d["label"],
                defaults={"strength_1_to_10": d["strength"]},
            )
        self.stdout.write("  interests ok")

        # ------------------------------------------------------------------ #
        # Questions
        #
        # Scope legend:
        #   q0  global          text    "Describe your greatest professional achievement."
        #   q1  Acme Corp       yesno   "Are you comfortable working fully remote?"
        #   q2  Acme / Backend  rating  "Rate your Django experience (1-10)."
        #   q3  Acme / PM       text    "Describe your product management philosophy."
        #   q4  Globex          single  "Which best describes your current role?"
        #   q5  Globex / DS     multi   "Which ML frameworks have you used?"
        #   q6  Initech         yesno   "Do you have experience with CI/CD pipelines?"
        #   q7  Initech / QA    rating  "Rate your automated testing experience (1-10)."
        #   q8  Umbrella        text    "Describe a security incident you have handled."
        #   q9  Umbrella / SR   single  "Which security domain is your primary focus?"
        # ------------------------------------------------------------------ #
        question_data = [
            # [0] global
            {"company": None,         "position": None,         "type": Question.TYPE_TEXT,   "prompt": "Describe your greatest professional achievement."},
            # [1] Acme Corp
            {"company": companies[0], "position": None,         "type": Question.TYPE_YESNO,  "prompt": "Are you comfortable working fully remote?"},
            # [2] Acme Corp / Backend Engineer
            {"company": companies[0], "position": positions[0], "type": Question.TYPE_RATING, "prompt": "Rate your Django experience (1-10)."},
            # [3] Acme Corp / Product Manager
            {"company": companies[0], "position": positions[1], "type": Question.TYPE_TEXT,   "prompt": "Describe your product management philosophy."},
            # [4] Globex
            {"company": companies[1], "position": None,         "type": Question.TYPE_SINGLE, "prompt": "Which best describes your current role?"},
            # [5] Globex / Data Scientist
            {"company": companies[1], "position": positions[2], "type": Question.TYPE_MULTI,  "prompt": "Which ML frameworks have you used?"},
            # [6] Initech
            {"company": companies[2], "position": None,         "type": Question.TYPE_YESNO,  "prompt": "Do you have experience with CI/CD pipelines?"},
            # [7] Initech / QA Engineer
            {"company": companies[2], "position": positions[3], "type": Question.TYPE_RATING, "prompt": "Rate your automated testing experience (1-10)."},
            # [8] Umbrella Co
            {"company": companies[3], "position": None,         "type": Question.TYPE_TEXT,   "prompt": "Describe a security incident you have handled."},
            # [9] Umbrella Co / Security Researcher
            {"company": companies[3], "position": positions[4], "type": Question.TYPE_SINGLE, "prompt": "Which security domain is your primary focus?"},
        ]
        questions = []
        for d in question_data:
            q, _ = Question.objects.get_or_create(
                company=d["company"], position=d["position"], prompt=d["prompt"],
                defaults={"question_type": d["type"]},
            )
            questions.append(q)
        self.stdout.write("  questions ok")

        # ------------------------------------------------------------------ #
        # QuestionChoices
        #   q4 (Globex single):       ic, manager
        #   q5 (Globex/DS multi):     tensorflow, pytorch, sklearn
        #   q9 (Umbrella/SR single):  appsec, pen-testing, threat-intel
        # ------------------------------------------------------------------ #
        choice_data = [
            # q4
            {"question": questions[4], "label": "Individual Contributor", "value": "ic",           "sort": 0},  # [0]
            {"question": questions[4], "label": "Manager",                "value": "manager",      "sort": 1},  # [1]
            # q5
            {"question": questions[5], "label": "TensorFlow",             "value": "tensorflow",   "sort": 0},  # [2]
            {"question": questions[5], "label": "PyTorch",                "value": "pytorch",      "sort": 1},  # [3]
            {"question": questions[5], "label": "scikit-learn",           "value": "sklearn",      "sort": 2},  # [4]
            # q9
            {"question": questions[9], "label": "Application Security",   "value": "appsec",       "sort": 0},  # [5]
            {"question": questions[9], "label": "Penetration Testing",    "value": "pen-testing",  "sort": 1},  # [6]
            {"question": questions[9], "label": "Threat Intelligence",    "value": "threat-intel", "sort": 2},  # [7]
        ]
        choices = []
        for d in choice_data:
            ch, _ = QuestionChoice.objects.get_or_create(
                question=d["question"], value=d["value"],
                defaults={"label": d["label"], "sort_order": d["sort"]},
            )
            choices.append(ch)
        self.stdout.write("  question choices ok")

        # ------------------------------------------------------------------ #
        # Submissions (5) — one per candidate/position pair
        # ------------------------------------------------------------------ #
        submission_data = [
            # [0] John -> Backend Engineer (Acme)   questions: q0, q1, q2
            {"candidate": candidates[0], "position": positions[0], "status": Submission.STATUS_FINISHED, "finished_at": timezone.now()},
            # [1] Jane -> Product Manager (Acme)    questions: q0, q1, q3
            {"candidate": candidates[1], "position": positions[1], "status": Submission.STATUS_FINISHED, "finished_at": timezone.now()},
            # [2] Carlos -> Data Scientist (Globex) questions: q0, q4, q5
            {"candidate": candidates[2], "position": positions[2], "status": Submission.STATUS_FINISHED, "finished_at": timezone.now()},
            # [3] Mei -> QA Engineer (Initech)      questions: q0, q6, q7
            {"candidate": candidates[3], "position": positions[3], "status": Submission.STATUS_DISCARDED, "finished_at": None},
            # [4] Omar -> Security Researcher (Umbrella) questions: q0, q8, q9
            {"candidate": candidates[4], "position": positions[4], "status": Submission.STATUS_NEW, "finished_at": None},
        ]
        submissions = []
        for d in submission_data:
            s, _ = Submission.objects.get_or_create(
                candidate=d["candidate"], position=d["position"],
                defaults={"status": d["status"], "finished_at": d["finished_at"]},
            )
            submissions.append(s)
        self.stdout.write("  submissions ok")

        # ------------------------------------------------------------------ #
        # Answers — complete coverage per submission
        #
        # submissions[0]: q0(text), q1(yesno), q2(rating)
        # submissions[1]: q0(text), q1(yesno), q3(text)
        # submissions[2]: q0(text), q4(single), q5(multi via AnswerChoice)
        # submissions[3]: q0(text), q6(yesno), q7(rating)
        # submissions[4]: q0(text), q8(text), q9(single)
        # ------------------------------------------------------------------ #
        answer_data = [
            # submissions[0] — Backend Engineer (Acme)
            {"sub": submissions[0], "q": questions[0], "text_value": "Architected a microservices platform that cut deployment time by 60%."},
            {"sub": submissions[0], "q": questions[1], "bool_value": True},
            {"sub": submissions[0], "q": questions[2], "int_value": 8},
            # submissions[1] — Product Manager (Acme)
            {"sub": submissions[1], "q": questions[0], "text_value": "Launched a B2B SaaS product from 0 to 200 paying customers in 12 months."},
            {"sub": submissions[1], "q": questions[1], "bool_value": False},
            {"sub": submissions[1], "q": questions[3], "text_value": "Ship fast, learn from real users, iterate relentlessly."},
            # submissions[2] — Data Scientist (Globex)
            {"sub": submissions[2], "q": questions[0], "text_value": "Led a team that shipped a real-time analytics dashboard serving 2M users."},
            {"sub": submissions[2], "q": questions[4], "choice": choices[0]},   # Individual Contributor
            # q5 (multi) handled below via AnswerChoice
            # submissions[3] — QA Engineer (Initech)
            {"sub": submissions[3], "q": questions[0], "text_value": "Caught a critical race condition before it reached production."},
            {"sub": submissions[3], "q": questions[6], "bool_value": True},
            {"sub": submissions[3], "q": questions[7], "int_value": 7},
            # submissions[4] — Security Researcher (Umbrella)
            {"sub": submissions[4], "q": questions[0], "text_value": "Discovered and responsibly disclosed a CVSS 9.8 vulnerability in a widely used library."},
            {"sub": submissions[4], "q": questions[8], "text_value": "Responded to a ransomware attack; contained the breach and restored services within 4 hours."},
            {"sub": submissions[4], "q": questions[9], "choice": choices[6]},   # Penetration Testing
        ]
        for d in answer_data:
            defaults = {}
            if "int_value"  in d: defaults["int_value"]  = d["int_value"]
            if "bool_value" in d: defaults["bool_value"] = d["bool_value"]
            if "text_value" in d: defaults["text_value"] = d["text_value"]
            if "choice"     in d: defaults["choice"]     = d["choice"]
            Answer.objects.get_or_create(
                submission=d["sub"], question=d["q"],
                defaults=defaults,
            )
        self.stdout.write("  answers ok")

        # ------------------------------------------------------------------ #
        # AnswerChoices — multi-select for submissions[2] / q5
        # Carlos selected: TensorFlow, PyTorch, scikit-learn
        # ------------------------------------------------------------------ #
        multi_answer, _ = Answer.objects.get_or_create(
            submission=submissions[2], question=questions[5],
        )
        for ch in choices[2:5]:  # tensorflow, pytorch, sklearn
            AnswerChoice.objects.get_or_create(answer=multi_answer, choice=ch)
        self.stdout.write("  answer choices ok")

        # ------------------------------------------------------------------ #
        # Notes (5)
        # ------------------------------------------------------------------ #
        alice = User.objects.get(username="alice.admin@example.com")
        note_data = [
            {"candidate": candidates[0], "body": "Strong Python background. Recommend fast-track interview."},
            {"candidate": candidates[1], "body": "Interesting pivot from marketing. Follow up on technical depth."},
            {"candidate": candidates[2], "body": "Excellent ML portfolio. Top candidate for Data Scientist role."},
            {"candidate": candidates[3], "body": "Solid DevOps chops but availability is limited to 20h/week."},
            {"candidate": candidates[4], "body": "Security certifications are current. Schedule technical screen."},
        ]
        for d in note_data:
            Note.objects.get_or_create(candidate=d["candidate"], author=alice, body=d["body"])
        self.stdout.write("  notes ok")

        # ------------------------------------------------------------------ #
        # ApplicationTokens (5)
        # ------------------------------------------------------------------ #
        for cand in candidates:
            ApplicationToken.objects.get_or_create(candidate=cand)
        self.stdout.write("  application tokens ok")

        self.stdout.write(self.style.SUCCESS('Sample data populated successfully'))
