from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse

from base.models import Candidate, Position, Question, Submission


class ApplicationFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("populate_sample_data")
        cls.position = Position.objects.get(title="Backend Engineer")

    def setUp(self):
        self.client = Client()

    def test_page_one_creates_candidate_and_logs_them_in(self):
        response = self.client.post(
            reverse("application", args=[self.position.id, 1]),
            data={
                "first_name": "Test",
                "last_name": "Applicant",
                "email": "test@fbstudios.com",
                "phone": "555-1212",
                "linkedin_url": "https://example.com/in/test-applicant",
                "bio": "Built a lot of things.",
            },
        )

        self.assertRedirects(response, reverse("application", args=[self.position.id, 2]))
        candidate = Candidate.objects.get(email="test@fbstudios.com")
        self.assertEqual(len(candidate.continue_code), 6)
        self.assertTrue(candidate.user_id)
        self.assertIn("_auth_user_id", self.client.session)

    def test_page_one_shows_errors_without_wiping_values(self):
        response = self.client.post(
            reverse("application", args=[self.position.id, 1]),
            data={
                "first_name": "Test",
                "last_name": "Applicant",
                "email": "not-an-email",
                "phone": "555-1313",
                "linkedin_url": "",
                "bio": "Still here",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enter a valid email address.")
        self.assertContains(response, 'value="Test"')
        self.assertContains(response, "Still here")

    def test_continue_application_logs_candidate_back_in(self):
        self.client.post(
            reverse("application", args=[self.position.id, 1]),
            data={
                "first_name": "Resume",
                "last_name": "Me",
                "email": "resume@fbstudios.com",
                "phone": "555-1414",
                "linkedin_url": "",
                "bio": "",
            },
        )
        candidate = Candidate.objects.get(email="resume@fbstudios.com")
        self.client.logout()

        response = self.client.post(
            reverse("application_continue"),
            data={
                "email": "resume@fbstudios.com",
                "continue_code": candidate.continue_code,
                "next": reverse("application", args=[self.position.id, 2]),
            },
        )

        self.assertRedirects(response, reverse("application", args=[self.position.id, 2]))
        self.assertIn("_auth_user_id", self.client.session)

    def test_page_one_rejects_existing_candidate_email_for_new_signup(self):
        existing_candidate = Candidate.objects.filter(user__isnull=False).first()

        response = self.client.post(
            reverse("application", args=[self.position.id, 1]),
            data={
                "first_name": "Someone",
                "last_name": "Else",
                "email": existing_candidate.email,
                "phone": "555-8888",
                "linkedin_url": "",
                "bio": "Trying again.",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "An application already exists for this email.")
        self.assertContains(response, "Continue an existing application")

    def test_page_two_submission_finishes_application(self):
        self.client.post(
            reverse("application", args=[self.position.id, 1]),
            data={
                "first_name": "Finish",
                "last_name": "Flow",
                "email": "finish@fbstudios.com",
                "phone": "555-1515",
                "linkedin_url": "",
                "bio": "",
            },
        )

        post_data = {}
        for question in Question.objects.filter(is_active=True, page=2).order_by("id"):
            if question.position_id and question.position_id != self.position.id:
                continue
            if question.company_id and question.position_id is None and question.company_id != self.position.company_id:
                continue

            if question.question_type == Question.TYPE_TEXT:
                post_data[f"question_{question.id}"] = "Here is a thoughtful answer."
            elif question.question_type == Question.TYPE_YESNO:
                post_data[f"question_{question.id}"] = "true"
            elif question.question_type == Question.TYPE_RATING:
                post_data[f"question_{question.id}"] = "8"

        response = self.client.post(reverse("application", args=[self.position.id, 2]), data=post_data)

        self.assertRedirects(response, "/submit_application/")
        submission = Submission.objects.filter(position=self.position, candidate__email="finish@fbstudios.com").latest("created_at")
        self.assertEqual(submission.status, Submission.STATUS_FINISHED)
        self.assertIsNotNone(submission.finished_at)

    def test_staff_user_gets_redirected_from_application_to_dashboard(self):
        admin_user = User.objects.get(username="alice.admin@example.com")
        self.client.force_login(admin_user)

        response = self.client.get(reverse("application", args=[self.position.id, 1]))

        self.assertRedirects(response, f"/dashboard/?company_id={self.position.company_id}")

    def test_company_admin_can_create_company_wide_question(self):
        admin_user = User.objects.get(username="alice.admin@example.com")
        self.client.force_login(admin_user)

        response = self.client.post(
            reverse("question_manager") + f"?company_id={self.position.company_id}",
            data={
                "company_id": self.position.company_id,
                "scope": "company",
                "prompt": "Do you enjoy collaborating across teams?",
                "help_text": "Short answer is fine.",
                "question_type": Question.TYPE_TEXT,
                "is_required": "on",
                "page": 2,
                "sort_order": 5,
                "choice_labels": "",
            },
        )

        self.assertRedirects(response, f"/dashboard/questions/?company_id={self.position.company_id}")
        self.assertTrue(
            Question.objects.filter(
                company=self.position.company,
                position__isnull=True,
                prompt="Do you enjoy collaborating across teams?",
            ).exists()
        )

    def test_company_admin_can_edit_company_question(self):
        admin_user = User.objects.get(username="alice.admin@example.com")
        self.client.force_login(admin_user)
        question = Question.objects.filter(company=self.position.company, position__isnull=True).first()

        response = self.client.post(
            reverse("edit_question", args=[question.id]),
            data={
                "company_id": self.position.company_id,
                "scope": "company",
                "prompt": "Updated collaboration question",
                "help_text": "Updated help text",
                "question_type": question.question_type,
                "is_required": "on",
                "page": 3,
                "sort_order": 9,
                "choice_labels": "",
            },
        )

        self.assertRedirects(response, f"/dashboard/questions/?company_id={self.position.company_id}")
        question.refresh_from_db()
        self.assertEqual(question.prompt, "Updated collaboration question")
        self.assertEqual(question.page, 3)
        self.assertEqual(question.sort_order, 9)

    def test_company_admin_can_archive_and_restore_question(self):
        admin_user = User.objects.get(username="alice.admin@example.com")
        self.client.force_login(admin_user)
        question = Question.objects.filter(company=self.position.company, position__isnull=True).first()

        response = self.client.post(reverse("archive_question", args=[question.id]))
        self.assertRedirects(response, f"/dashboard/questions/?company_id={self.position.company_id}")
        question.refresh_from_db()
        self.assertFalse(question.is_active)

        response = self.client.post(reverse("archive_question", args=[question.id]))
        self.assertRedirects(response, f"/dashboard/questions/?company_id={self.position.company_id}")
        question.refresh_from_db()
        self.assertTrue(question.is_active)
