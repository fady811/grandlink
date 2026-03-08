from django.db import migrations


def migrate_skills(apps, schema_editor):
    """
    Migrates skills data from the 'skills_legacy' JSONField to the new 'skills' ManyToManyField.
    If a skill name in the JSON list doesn't already exist in the Skill table, it's created.
    """
    StudentProfile = apps.get_model('profiles', 'StudentProfile')
    Skill = apps.get_model('jobs', 'Skill')

    for profile in StudentProfile.objects.all():
        # Get the old list of strings: ["Python", "Django", ...]
        skills_list = profile.skills_legacy
        if not isinstance(skills_list, list):
            continue

        for skill_name in skills_list:
            skill_name = str(skill_name).strip()
            if not skill_name:
                continue

            # Create or get the Skill instance
            skill_obj, created = Skill.objects.get_or_create(
                name__iexact=skill_name,
                defaults={'name': skill_name, 'category': 'technical'}
            )
            # Add to the profile's ManyToMany relation
            profile.skills.add(skill_obj)


def reverse_skills(apps, schema_editor):
    """
    Reverse migration: copies data back from'skills' to 'skills_legacy'.
    Useful in case of rollback.
    """
    # ... logic here if needed, but not strictly required.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0002_employerprofile_logo_studentprofile_skills_legacy_and_more'),
    ]

    operations = [
        migrations.RunPython(migrate_skills, reverse_code=reverse_skills),
    ]
