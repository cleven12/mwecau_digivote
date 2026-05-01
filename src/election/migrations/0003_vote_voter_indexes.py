from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('election', '0002_seed_election_and_candidates'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='vote',
            index=models.Index(fields=['voter'], name='votes_voter_idx'),
        ),
        migrations.AddIndex(
            model_name='vote',
            index=models.Index(fields=['voter', 'election'], name='votes_voter_election_idx'),
        ),
    ]
