# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import uuid

from django.db import migrations, models


def fill_mymodel_uuid(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    MyModel = apps.get_model('myapp', 'MyModel')
    for obj in MyModel.objects.using(db_alias).all():
        obj.uuid = uuid.uuid4()
        obj.save()


class Migration(migrations.Migration):
    """ Change model with integer pk to UUID pk.  This migration presumes there
    are no db constraints (foreign keys) to this table.
    
    Note: this migration is not reversible.  See the comment above the
    `RemoveField` operation.  Further, this migration is possible in part due
    to the fact that there are currenty no foreign key restraints to this table.
    """

    dependencies = [
        # ...
    ]

    operations = [
        migrations.AddField(
            model_name='mymodel',
            name='uuid',
            field=models.UUIDField(null=True),
        ),
        migrations.RunPython(fill_mymodel_uuid, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='mymodel',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, unique=True),
        ),
        # this RemoveField operation is irreversible, because in order to
        # recreate it, the primary key constraint on the UUIDField would first
        # have to be dropped.
        migrations.RemoveField('MyModel', 'id'),
        migrations.RenameField(
            model_name='mymodel',
            old_name='uuid',
            new_name='id'
        ),
        migrations.AlterField(
            model_name='mymodel',
            name='id',
            field=models.UUIDField(primary_key=True, default=uuid.uuid4, serialize=False, editable=False, unique=True),
        ),
    ]
