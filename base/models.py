from django.db import models
import uuid


class Position(models.Model):
    """
    Job position within a company (e.g., Software Engineer, Sales Manager).
    Each company can have many positions.
    """
    EMPLOYMENT_FULL_TIME = "full_time"
    EMPLOYMENT_PART_TIME = "part_time"
    EMPLOYMENT_TYPE_CHOICES = [
        (EMPLOYMENT_FULL_TIME, "Full-time"),
        (EMPLOYMENT_PART_TIME, "Part-time"),
    ]

    external_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    company = models.ForeignKey('Company', on_delete=models.CASCADE, related_name="positions")
    created_by = models.ForeignKey(
        "auth.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="created_positions"
    )
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    employment_type = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_TYPE_CHOICES,
        default=EMPLOYMENT_FULL_TIME,
        db_index=True,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} @ {self.company.title}"


class Company(models.Model):
    """
    A company inside your greater org (espresso repair, 2A startup, vehicle ads, etc).
    Candidates can be recruited across companies, and staff can operate per-company.
    """
    external_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    created_by = models.ForeignKey(
        "auth.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="created_companies"
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class CompanyStaff(models.Model):
    """
    A user linked to exactly ONE company as "their" admin/staff company.
    (If later you want staff to span companies, change unique constraint.)
    """
    user = models.OneToOneField("auth.User", on_delete=models.CASCADE, related_name="company_staff")
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="staff")

    # keep it simple: admin vs staff
    is_admin = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} @ {self.company}"


class Candidate(models.Model):
    """
    Core person record. Optional link to auth.User so candidates can log in.
    """
    external_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    user = models.OneToOneField(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="candidate_profile",
    )

    email = models.EmailField(db_index=True)
    first_name = models.CharField(max_length=80, blank=True)
    last_name = models.CharField(max_length=80, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    linkedin_url = models.URLField(blank=True)

    # freeform summary written by the candidate
    bio = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["email"], name="uniq_candidate_email"),
        ]
        indexes = [
            models.Index(fields=["last_name", "first_name"]),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email


class CandidateInterest(models.Model):
    """
    Lightweight "interest graph" that makes cross-company matching easy.
    Examples: cars, guns, coffee, python, sportscars, etc.
    """
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="interests")
    slug = models.SlugField()  # e.g. "cars", "guns", "python"
    label = models.CharField(max_length=120)  # e.g. "Cars", "Guns", "Python"
    strength_1_to_10 = models.PositiveSmallIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["candidate", "slug"], name="uniq_candidate_interest_key"),
        ]

    def __str__(self):
        return f"{self.candidate} -> {self.key}"


class Note(models.Model):
    """
    Internal notes written by staff/admins about a candidate.
    Replaces the old admin_notes TextField on Candidate.
    """
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="notes")
    author = models.ForeignKey(
        "auth.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="authored_notes"
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Note by {self.author} on {self.candidate}"


class Submission(models.Model):
    """
    Holds job aplication data for a candidate.
    If candidate is not logged in, using a new email is enforced.
    Status becomes finished once candidate submits it.
    """
    external_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    position = models.ForeignKey(
        Position, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True, 
        related_name="submissions"
    )

    candidate = models.ForeignKey(
        Candidate, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="submissions"
    )

    # snapshot of what they submitted
    payload = models.JSONField(default=dict, blank=True)

    # resolution workflow
    STATUS_NEW = "new"
    STATUS_DISCARDED = "discarded"
    STATUS_FINISHED = "finished"
    status = models.CharField(
        max_length=20,
        choices=[
            (STATUS_NEW, "New"),
            (STATUS_DISCARDED, "Discarded"),
            (STATUS_FINISHED, "Finished"),
        ],
        default=STATUS_NEW,
        db_index=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    edited_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.company.slug}:{self.candidate} ({self.status})"


class Question(models.Model):
    """
    Custom questions.
    """
    external_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # If company is null, question is global
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="questions",
    )

    # If position is null, question is company-wide
    position = models.ForeignKey(
        'Position',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='questions',
    )

    # question “shape”
    TYPE_RATING = "rating"      # usually 1-10
    TYPE_YESNO = "yesno"        # bool
    TYPE_TEXT = "text"          # free text
    TYPE_SINGLE = "single"      # single choice
    TYPE_MULTI = "multi"        # multi choice
    question_type = models.CharField(
        max_length=20,
        choices=[
            (TYPE_RATING, "Rating"),
            (TYPE_YESNO, "Yes/No"),
            (TYPE_TEXT, "Text"),
            (TYPE_SINGLE, "Single choice"),
            (TYPE_MULTI, "Multi choice"),
        ],
        default=TYPE_RATING,
        db_index=True,
    )

    prompt = models.TextField()

    help_text = models.CharField(max_length=240, blank=True)

    is_required = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        scope = "global"
        if (self.postion_id):
            scope = self.position.title
        elif (self.company_id):
            scope = self.company.slug
        return f"[{scope}] {self.prompt[:60]}"


class QuestionChoice(models.Model):
    """
    Only used when question_type is single/multi.
    """
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    label = models.CharField(max_length=140)
    value = models.SlugField(max_length=140)  # stable machine value
    sort_order = models.IntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["question", "value"], name="uniq_choice_value_per_question"),
        ]

    def __str__(self):
        return f"{self.question_id}:{self.value}"


class CandidateAnswer(models.Model):
    """
    One row per (candidate, question).
    Stores different types in different columns.
    For multi-choice, we store selections in CandidateAnswerChoice.
    """
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")

    int_value = models.IntegerField(null=True, blank=True)
    bool_value = models.BooleanField(null=True, blank=True)
    text_value = models.TextField(blank=True)

    # single choice selection
    choice = models.ForeignKey(
        QuestionChoice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="selected_in_answers",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["candidate", "question"], name="uniq_candidate_question_answer"),
        ]
        indexes = [
            models.Index(fields=["question"]),
        ]

    def __str__(self):
        return f"{self.candidate_id}:{self.question_id}"


class CandidateAnswerChoice(models.Model):
    """
    Multi-select bridge table.
    """
    answer = models.ForeignKey(CandidateAnswer, on_delete=models.CASCADE, related_name="multi_choices")
    choice = models.ForeignKey(QuestionChoice, on_delete=models.CASCADE, related_name="multi_selected_in")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["answer", "choice"], name="uniq_answer_choice"),
        ]

    def __str__(self):
        return f"{self.answer_id}:{self.choice_id}"


class ApplicationToken(models.Model):
    """
    One-time magic link token for a candidate to resume or complete their application.
    Created when the candidate enters their email at the start of the application.
    Can be used multiple times. Expires after a week.
    """
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="application_tokens")
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Token for {self.candidate} (used: {self.used_at is not None})"