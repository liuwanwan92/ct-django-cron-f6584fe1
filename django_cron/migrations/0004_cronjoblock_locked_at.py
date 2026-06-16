from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_cron', '0003_cronjoblock'),
    ]

    operations = [
        migrations.AddField(
            model_name='cronjoblock',
            name='locked_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
