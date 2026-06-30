"""
Populate the database with demo data for local development and demos.

Usage:
    python manage.py seed_demo
    python manage.py seed_demo --clear   # wipe and re-seed
"""

from __future__ import annotations

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.comments.infrastructure.models import CommentRecord
from apps.feature_requests.infrastructure.models import (
    FeatureRequestRecord,
    StatusChangeLogRecord,
    VoteRecord,
)
from apps.identity.infrastructure.models import UserRecord

DEMO_PASSWORD = make_password("Demo1234!")

USERS = [
    {"email": "admin@demo.com", "display_name": "Admin", "role": "admin", "email_verified": True},
    {
        "email": "moderator@demo.com",
        "display_name": "Moderator",
        "role": "moderator",
        "email_verified": True,
    },
    {"email": "alice@demo.com", "display_name": "Alice", "role": "user", "email_verified": True},
    {"email": "bob@demo.com", "display_name": "Bob", "role": "user", "email_verified": True},
    {"email": "carol@demo.com", "display_name": "Carol", "role": "user", "email_verified": True},
]

FEATURE_REQUESTS = [
    {
        "title": "Dark mode support",
        "description": "Allow users to switch between light and dark themes. Essential for night-time usage and reduces eye strain.",
        "status": "planned",
        "author": "alice@demo.com",
    },
    {
        "title": "Export feature requests to CSV",
        "description": "Product managers need to analyse voting data offline. A one-click CSV export from the admin panel would save hours each week.",
        "status": "under_review",
        "author": "bob@demo.com",
    },
    {
        "title": "Email digest of top requests",
        "description": "Weekly summary email showing the top 10 voted requests so stakeholders stay informed without logging in.",
        "status": "open",
        "author": "carol@demo.com",
    },
    {
        "title": "Keyboard shortcuts for power users",
        "description": "Add J/K navigation, V to vote, and C to comment. Heavy users rely on keyboard-first workflows.",
        "status": "open",
        "author": "alice@demo.com",
    },
    {
        "title": "Bulk status transition for admins",
        "description": "Allow admins to select multiple requests and transition them all to 'declined' or 'shipped' in one action.",
        "status": "open",
        "author": "bob@demo.com",
    },
    {
        "title": "SSO / OAuth login",
        "description": "Support Google and GitHub OAuth so enterprise teams don't need to manage separate credentials.",
        "status": "in_progress",
        "author": "carol@demo.com",
    },
    {
        "title": "Public API for integrations",
        "description": "A read-only public API would let teams embed the feature voting widget in their own dashboards.",
        "status": "shipped",
        "author": "alice@demo.com",
    },
]

VOTES = {
    "Dark mode support": [
        "alice@demo.com",
        "bob@demo.com",
        "carol@demo.com",
        "admin@demo.com",
        "moderator@demo.com",
    ],
    "Export feature requests to CSV": ["alice@demo.com", "carol@demo.com", "admin@demo.com"],
    "Email digest of top requests": ["bob@demo.com", "carol@demo.com"],
    "Keyboard shortcuts for power users": ["alice@demo.com", "admin@demo.com"],
    "Bulk status transition for admins": ["admin@demo.com", "moderator@demo.com"],
    "SSO / OAuth login": ["alice@demo.com", "bob@demo.com", "carol@demo.com", "admin@demo.com"],
    "Public API for integrations": ["alice@demo.com", "bob@demo.com"],
}

COMMENTS = {
    "Dark mode support": [
        ("alice@demo.com", "This has been requested by our whole design team. +1 from everyone."),
        ("bob@demo.com", "Should respect the OS-level preference automatically too."),
        ("carol@demo.com", "OLED screens will thank you. Please prioritise this!"),
    ],
    "Export feature requests to CSV": [
        ("carol@demo.com", "I manually copy this data every Monday morning. Please ship this."),
        ("admin@demo.com", "Scoped to CSV for now; Excel support can come later."),
    ],
    "SSO / OAuth login": [
        (
            "bob@demo.com",
            "Google OAuth is blocking our enterprise trial. This is a blocker for us.",
        ),
        ("alice@demo.com", "GitHub OAuth would be great for developer-facing products too."),
    ],
    "Public API for integrations": [
        (
            "carol@demo.com",
            "Already shipped — just tested the /v1/feature-requests endpoint. Works great!",
        ),
    ],
}

STATUS_TRANSITIONS = [
    ("Dark mode support", "open", "planned", "moderator@demo.com", "Confirmed in roadmap for Q3."),
    (
        "Export feature requests to CSV",
        "open",
        "under_review",
        "moderator@demo.com",
        "Reviewing scope with the product team.",
    ),
    ("SSO / OAuth login", "open", "under_review", "moderator@demo.com", "Design doc in progress."),
    (
        "SSO / OAuth login",
        "under_review",
        "planned",
        "admin@demo.com",
        "Approved. Engineering picking it up next sprint.",
    ),
    ("SSO / OAuth login", "planned", "in_progress", "admin@demo.com", "Dev branch open."),
    (
        "Public API for integrations",
        "open",
        "under_review",
        "moderator@demo.com",
        "Scoping the auth model.",
    ),
    ("Public API for integrations", "under_review", "planned", "admin@demo.com", None),
    ("Public API for integrations", "planned", "in_progress", "admin@demo.com", None),
    (
        "Public API for integrations",
        "in_progress",
        "shipped",
        "admin@demo.com",
        "Deployed to production.",
    ),
]


class Command(BaseCommand):
    help = "Seed the database with demo users and feature requests."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing data before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["clear"]:
            self._clear()

        users = self._seed_users()
        frs = self._seed_feature_requests(users)
        self._seed_votes(users, frs)
        self._seed_status_transitions(users, frs)
        self._seed_comments(users, frs)

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone. {len(users)} users · {len(frs)} requests · "
                "votes, comments, and status transitions seeded.\n"
                "\nDemo credentials (password: Demo1234!):\n"
                "  admin@demo.com      — admin\n"
                "  moderator@demo.com  — moderator\n"
                "  alice@demo.com      — user\n"
            )
        )

    def _clear(self):
        CommentRecord.objects.all().delete()
        StatusChangeLogRecord.objects.all().delete()
        VoteRecord.objects.all().delete()
        FeatureRequestRecord.objects.all().delete()
        UserRecord.objects.filter(email__endswith="@demo.com").delete()
        self.stdout.write("Cleared existing demo data.")

    def _seed_users(self) -> dict[str, UserRecord]:
        users = {}
        for data in USERS:
            user, created = UserRecord.objects.get_or_create(
                email=data["email"],
                defaults={
                    "display_name": data["display_name"],
                    "role": data["role"],
                    "email_verified": data["email_verified"],
                    "password": DEMO_PASSWORD,
                },
            )
            users[data["email"]] = user
            if created:
                self.stdout.write(f"  Created user {user.email} ({user.role})")
        return users

    def _seed_feature_requests(
        self, users: dict[str, UserRecord]
    ) -> dict[str, FeatureRequestRecord]:
        frs = {}
        for data in FEATURE_REQUESTS:
            fr, created = FeatureRequestRecord.objects.get_or_create(
                title=data["title"],
                defaults={
                    "description": data["description"],
                    "status": data["status"],
                    "author": users[data["author"]],
                },
            )
            frs[data["title"]] = fr
            if created:
                self.stdout.write(f"  Created request '{fr.title}' [{fr.status}]")
        return frs

    def _seed_votes(self, users: dict[str, UserRecord], frs: dict[str, FeatureRequestRecord]):
        for title, voter_emails in VOTES.items():
            fr = frs[title]
            count = 0
            for email in voter_emails:
                _, created = VoteRecord.objects.get_or_create(feature_request=fr, user=users[email])
                if created:
                    count += 1
            if count:
                FeatureRequestRecord.objects.filter(pk=fr.pk).update(vote_count=len(voter_emails))

    def _seed_status_transitions(
        self, users: dict[str, UserRecord], frs: dict[str, FeatureRequestRecord]
    ):
        for title, from_s, to_s, actor_email, reason in STATUS_TRANSITIONS:
            fr = frs[title]
            StatusChangeLogRecord.objects.get_or_create(
                feature_request=fr,
                from_status=from_s,
                to_status=to_s,
                changed_by=users[actor_email],
                defaults={"reason": reason, "changed_at": timezone.now()},
            )

    def _seed_comments(self, users: dict[str, UserRecord], frs: dict[str, FeatureRequestRecord]):
        for title, entries in COMMENTS.items():
            fr = frs[title]
            for email, body in entries:
                CommentRecord.objects.get_or_create(
                    feature_request=fr,
                    author=users[email],
                    body=body,
                    defaults={"is_deleted": False, "is_hidden": False},
                )
