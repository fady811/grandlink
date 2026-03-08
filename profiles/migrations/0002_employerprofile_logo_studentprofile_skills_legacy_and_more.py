from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0001_initial'),
        ('profiles', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='employerprofile',
            name='logo',
            field=models.ImageField(blank=True, null=True, upload_to='company_logos/'),
        ),
        # 1. Rename existing JSONField 'skills' to 'skills_legacy'
        migrations.RenameField(
            model_name='studentprofile',
            old_name='skills',
            new_name='skills_legacy',
        ),
        # 2. Add new ManyToManyField 'skills'
        migrations.AddField(
            model_name='studentprofile',
            name='skills',
            field=models.ManyToManyField(blank=True, related_name='student_profiles', to='jobs.skill'),
        ),
    ]
