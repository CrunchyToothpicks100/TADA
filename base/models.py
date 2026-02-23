from django.db import models
import uuid


class Company(models.Model):
    """
    A company inside your greater org (espresso repair, 2A startup, vehicle ads, etc).
    Candidates can be recruited across companies, and staff can operate per-company.
    """
    external_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=160)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


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

    # freeform summary + internal notes (admins)
    bio = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)

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
    key = models.SlugField()  # e.g. "cars", "guns", "python"
    label = models.CharField(max_length=120)  # e.g. "Cars", "Guns", "Python"
    strength_1_to_10 = models.PositiveSmallIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["candidate", "key"], name="uniq_candidate_interest_key"),
        ]

    def __str__(self):
        return f"{self.candidate} -> {self.key}"


class IntakeSubmission(models.Model):
    """
    Stores a submitted form payload even if we couldn't create a User due to duplicate email.
    You can later "resolve" it by attaching it to the correct Candidate/User.
    """
    external_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="intake_submissions")
    email = models.EmailField(db_index=True)

    # snapshot of what they submitted
    payload = models.JSONField(default=dict, blank=True)

    # resolution workflow
    STATUS_NEW = "new"
    STATUS_NEEDS_EMAIL = "needs_email"  # duplicate email, told to use a different one
    STATUS_RESOLVED = "resolved"
    STATUS_DISCARDED = "discarded"
    status = models.CharField(
        max_length=20,
        choices=[
            (STATUS_NEW, "New"),
            (STATUS_NEEDS_EMAIL, "Needs Email"),
            (STATUS_RESOLVED, "Resolved"),
            (STATUS_DISCARDED, "Discarded"),
        ],
        default=STATUS_NEW,
        db_index=True,
    )

    resolved_candidate = models.ForeignKey(
        Candidate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_submissions",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.company.slug}:{self.email} ({self.status})"


class Question(models.Model):
    """
    Custom questions.
    - company = NULL means it is defined "globally"
    - is_global=True means "ask across the board" (even if owned by a company)
      This lets Company X invent a question, then promote it to everyone.
    """
    external_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="questions",
    )

    is_global = models.BooleanField(default=False, db_index=True)

    # who should see it (candidate form vs internal admin-only)
    AUD_CANDIDATE = "candidate"
    AUD_ADMIN = "admin"
    audience = models.CharField(
        max_length=20,
        choices=[
            (AUD_CANDIDATE, "Candidate"),
            (AUD_ADMIN, "Admin"),
        ],
        default=AUD_CANDIDATE,
        db_index=True,
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

    # for rating questions (defaults make your “1-10 everything” idea easy)
    min_value = models.PositiveSmallIntegerField(default=1)
    max_value = models.PositiveSmallIntegerField(default=10)

    is_required = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["company", "is_active", "audience"]),
            models.Index(fields=["is_global", "is_active", "audience"]),
        ]

    def __str__(self):
        scope = self.company.slug if self.company_id else "global"
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