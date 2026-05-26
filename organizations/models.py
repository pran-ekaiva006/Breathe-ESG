from django.conf import settings
from django.db import models


class Organization(models.Model):
    """A tenant organization in the BreatheESG platform."""

    name = models.CharField(max_length=255)
    industry = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class UserOrganization(models.Model):
    """Maps users to organizations with a specific role."""

    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        ANALYST = "analyst", "Analyst"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_organizations",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="user_organizations",
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ANALYST,
    )

    class Meta:
        unique_together = ("user", "organization")

    def __str__(self):
        return f"{self.user} — {self.organization} ({self.get_role_display()})"

