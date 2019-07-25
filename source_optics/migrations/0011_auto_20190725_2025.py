# Generated by Django 2.2.2 on 2019-07-25 20:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('source_optics', '0010_auto_20190724_1958'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='repository',
            options={},
        ),
        migrations.RemoveField(
            model_name='author',
            name='repos',
        ),
        migrations.AddField(
            model_name='filechange',
            name='file',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='source_optics.File'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='credential',
            name='name',
            field=models.TextField(db_index=True, max_length=64),
        ),
        migrations.AlterField(
            model_name='organization',
            name='name',
            field=models.TextField(db_index=True, max_length=32, unique=True),
        ),
        migrations.AlterField(
            model_name='repository',
            name='url',
            field=models.TextField(db_index=True, help_text='use a git ssh url for private repos, else http/s are ok', max_length=255),
        ),
        migrations.AlterUniqueTogether(
            name='commit',
            unique_together={('repo', 'sha')},
        ),
        migrations.AlterUniqueTogether(
            name='file',
            unique_together={('repo', 'name', 'path', 'ext')},
        ),
        migrations.AlterUniqueTogether(
            name='filechange',
            unique_together={('file', 'commit')},
        ),
        migrations.AddIndex(
            model_name='author',
            index=models.Index(fields=['email'], name='source_opti_email_d3e229_idx'),
        ),
        migrations.AddIndex(
            model_name='commit',
            index=models.Index(fields=['author_date', 'author', 'repo'], name='source_opti_author__cbf24f_idx'),
        ),
        migrations.AddIndex(
            model_name='repository',
            index=models.Index(fields=['name', 'organization'], name='source_opti_name_5846e6_idx'),
        ),
        migrations.RemoveField(
            model_name='commit',
            name='files',
        ),
        migrations.RemoveField(
            model_name='commit',
            name='lines_added',
        ),
        migrations.RemoveField(
            model_name='commit',
            name='lines_removed',
        ),
        migrations.RemoveField(
            model_name='file',
            name='changes',
        ),
        migrations.RemoveField(
            model_name='file',
            name='lines_added',
        ),
        migrations.RemoveField(
            model_name='file',
            name='lines_removed',
        ),
        migrations.RemoveField(
            model_name='filechange',
            name='binary',
        ),
        migrations.RemoveField(
            model_name='filechange',
            name='ext',
        ),
        migrations.RemoveField(
            model_name='filechange',
            name='name',
        ),
        migrations.RemoveField(
            model_name='filechange',
            name='path',
        ),
        migrations.RemoveField(
            model_name='filechange',
            name='repo',
        ),
    ]
