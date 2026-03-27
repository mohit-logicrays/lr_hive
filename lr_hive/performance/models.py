from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import (
    ActivatorModel,
    TimeStampedModel,
    TitleSlugDescriptionModel,
)


class PerformanceQuestion(TitleSlugDescriptionModel, TimeStampedModel, ActivatorModel):
    """Performance question model used in reviews."""

    class Meta:
        verbose_name = _("Performance Question")
        verbose_name_plural = _("Performance Questions")

    def __str__(self):
        return self.title


class PerformanceReview(TimeStampedModel, ActivatorModel):
    """Container for a performance review session."""

    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="performance_reviews_given",
        help_text=_("Reviewer"),
    )
    reviewee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="performance_reviews_received",
        help_text=_("Reviewee"),
    )
    organization = models.ForeignKey(
        "organization.Organization",
        on_delete=models.CASCADE,
        related_name="performance_reviews",
        help_text=_("Organization"),
    )

    class Meta:
        verbose_name = _("Performance Review")
        verbose_name_plural = _("Performance Reviews")
        indexes = [
            models.Index(fields=["reviewer"]),
            models.Index(fields=["reviewee"]),
            models.Index(fields=["organization"]),
        ]

    def __str__(self):
        return f"{self.reviewer} reviewing {self.reviewee}"

    @property
    def overall_score(self):
        """Calculate the average score for this review."""
        scores = self.answers.all().values_list("score", flat=True)
        if not scores:
            return 0
        return sum(scores) / len(scores)


class PerformanceReviewAnswer(TimeStampedModel, ActivatorModel):
    """Score and comment for a specific question in a review."""

    performance_review = models.ForeignKey(
        "performance.PerformanceReview",
        on_delete=models.CASCADE,
        related_name="answers",
        help_text=_("Performance Review"),
    )
    performance_question = models.ForeignKey(
        "performance.PerformanceQuestion",
        on_delete=models.CASCADE,
        related_name="answers",
        help_text=_("Performance Question"),
    )
    score = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_("Score from 1 to 5"),
    )
    comment = models.TextField(blank=True, help_text=_("Comment"))

    class Meta:
        verbose_name = _("Performance Review Answer")
        verbose_name_plural = _("Performance Review Answers")
