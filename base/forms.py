from django import forms
from django.utils.text import slugify

from base.models import Candidate, Interest, Question, SubmissionNote


class CandidateForm(forms.ModelForm):
    interests = forms.ModelMultipleChoiceField(
        queryset=Interest.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Candidate
        fields = ["first_name", "last_name", "email", "phone", "linkedin_url", "bio"]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, interest_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["interests"].queryset = interest_queryset if interest_queryset is not None else Interest.objects.none()

        candidate = self.instance if getattr(self.instance, "pk", None) else None
        if candidate is not None:
            selected_ids = candidate.interests.exclude(interest__isnull=True).values_list("interest_id", flat=True)
            self.fields["interests"].initial = list(selected_ids)

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean_first_name(self):
        return self.cleaned_data["first_name"].strip()

    def clean_last_name(self):
        return self.cleaned_data["last_name"].strip()

    def clean_phone(self):
        return self.cleaned_data["phone"].strip()

    def clean_linkedin_url(self):
        return self.cleaned_data["linkedin_url"].strip()

    def clean_bio(self):
        return self.cleaned_data["bio"].strip()


class ContinueApplicationForm(forms.Form):
    email = forms.EmailField()
    continue_code = forms.CharField(max_length=6, min_length=6)

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean_continue_code(self):
        code = "".join(ch for ch in self.cleaned_data["continue_code"] if ch.isdigit())
        if len(code) != 6:
            raise forms.ValidationError("Enter the 6-digit code from your application.")
        return code


class QuestionForm(forms.Form):
    def __init__(self, *args, questions, answers_by_question_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.questions = list(questions)
        self.answers_by_question_id = answers_by_question_id or {}

        for question in self.questions:
            self.fields[self.field_name(question)] = self.build_field(question)
            self.initial[self.field_name(question)] = self.initial_value(question)

    @staticmethod
    def field_name(question):
        return f"question_{question.id}"

    def build_field(self, question):
        common_kwargs = {
            "label": question.prompt,
            "help_text": question.help_text,
            "required": question.is_required,
        }

        if question.question_type == Question.TYPE_TEXT:
            return forms.CharField(widget=forms.Textarea(attrs={"rows": 5}), **common_kwargs)

        if question.question_type == Question.TYPE_RATING:
            return forms.IntegerField(min_value=1, max_value=10, **common_kwargs)

        if question.question_type == Question.TYPE_YESNO:
            return forms.TypedChoiceField(
                choices=[("", "Select one"), ("true", "Yes"), ("false", "No")],
                coerce=lambda value: value == "true",
                empty_value=None,
                **common_kwargs,
            )

        choice_values = [(choice.value, choice.label) for choice in question.choices.order_by("sort_order", "id")]
        if question.question_type == Question.TYPE_SINGLE:
            return forms.ChoiceField(choices=[("", "Select one"), *choice_values], **common_kwargs)

        if question.question_type == Question.TYPE_MULTI:
            return forms.MultipleChoiceField(
                choices=choice_values,
                widget=forms.CheckboxSelectMultiple,
                **common_kwargs,
            )

        return forms.CharField(**common_kwargs)

    def initial_value(self, question):
        answer = self.answers_by_question_id.get(question.id)
        if not answer:
            return None

        if question.question_type == Question.TYPE_TEXT:
            return answer.text_value
        if question.question_type == Question.TYPE_RATING:
            return answer.int_value
        if question.question_type == Question.TYPE_YESNO:
            if answer.bool_value is None:
                return ""
            return "true" if answer.bool_value else "false"
        if question.question_type == Question.TYPE_SINGLE:
            return answer.choice.value if answer.choice_id else ""
        if question.question_type == Question.TYPE_MULTI:
            return [selection.choice.value for selection in answer.multi_choices.all()]
        return None


class QuestionBuilderForm(forms.Form):
    scope = forms.ChoiceField()
    prompt = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}))
    help_text = forms.CharField(max_length=240, required=False)
    question_type = forms.ChoiceField(choices=Question._meta.get_field("question_type").choices)
    is_required = forms.BooleanField(required=False)
    page = forms.IntegerField(min_value=2, initial=2)
    sort_order = forms.IntegerField(initial=0)
    choice_labels = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text="For single or multi choice questions, enter one option per line.",
    )

    def __init__(self, *args, include_position_scope=False, question=None, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [
            ("global", "Global (every application)"),
            ("company", "Company-wide (every job for this company)"),
        ]
        if include_position_scope:
            choices.append(("position", "Position-specific"))
        self.fields["scope"].choices = choices
        self.question = question

        if question is not None:
            if question.position_id:
                scope = "position"
            elif question.company_id:
                scope = "company"
            else:
                scope = "global"

            self.fields["scope"].initial = scope
            self.fields["scope"].disabled = True
            self.fields["prompt"].initial = question.prompt
            self.fields["help_text"].initial = question.help_text
            self.fields["question_type"].initial = question.question_type
            self.fields["question_type"].disabled = True
            self.fields["is_required"].initial = question.is_required
            self.fields["page"].initial = question.page
            self.fields["sort_order"].initial = question.sort_order
            self.fields["choice_labels"].initial = "\n".join(
                question.choices.order_by("sort_order", "id").values_list("label", flat=True)
            )

    def clean_choice_labels(self):
        raw_value = self.cleaned_data["choice_labels"]
        labels = [line.strip() for line in raw_value.splitlines() if line.strip()]
        question_type = self.cleaned_data.get("question_type")
        if self.question is not None:
            question_type = self.question.question_type
        if question_type in {Question.TYPE_SINGLE, Question.TYPE_MULTI} and not labels:
            raise forms.ValidationError("Add at least one choice for single or multi choice questions.")
        return labels

    def build_choices(self):
        labels = self.cleaned_data["choice_labels"]
        used_values = set()
        built = []
        for index, label in enumerate(labels):
            value = slugify(label)[:140] or f"choice-{index + 1}"
            original_value = value
            suffix = 2
            while value in used_values:
                value = f"{original_value[:130]}-{suffix}"
                suffix += 1
            used_values.add(value)
            built.append({"label": label, "value": value, "sort_order": index})
        return built


class SubmissionNoteForm(forms.ModelForm):
    class Meta:
        model = SubmissionNote
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 4}),
        }
