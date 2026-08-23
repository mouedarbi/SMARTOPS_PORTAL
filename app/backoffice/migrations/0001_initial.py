from django.db import migrations, models


def create_triggers(apps, schema_editor):
    vendor = schema_editor.connection.vendor
    with schema_editor.connection.cursor() as cursor:
        if vendor == 'sqlite':
            cursor.executescript("""
            CREATE TRIGGER IF NOT EXISTS audit_license_insert
            AFTER INSERT ON licensing_license
            BEGIN
                INSERT INTO backoffice_databaseauditlog (action, table_name, row_id, old_values, new_values, timestamp)
                VALUES (
                    'INSERT',
                    'licensing_license',
                    NEW.id,
                    NULL,
                    'License Key: ' || NEW.license_key || ' | User ID: ' || NEW.user_id || ' | Module ID: ' || NEW.module_id || ' | Active: ' || NEW.is_active,
                    datetime('now')
                );
            END;

            CREATE TRIGGER IF NOT EXISTS audit_license_update
            AFTER UPDATE ON licensing_license
            BEGIN
                INSERT INTO backoffice_databaseauditlog (action, table_name, row_id, old_values, new_values, timestamp)
                VALUES (
                    'UPDATE',
                    'licensing_license',
                    NEW.id,
                    'Active: ' || OLD.is_active || ' | Activations: ' || OLD.activation_count || ' | Installation ID: ' || COALESCE(OLD.installation_id, 'NULL'),
                    'Active: ' || NEW.is_active || ' | Activations: ' || NEW.activation_count || ' | Installation ID: ' || COALESCE(NEW.installation_id, 'NULL'),
                    datetime('now')
                );
            END;

            CREATE TRIGGER IF NOT EXISTS audit_license_delete
            AFTER DELETE ON licensing_license
            BEGIN
                INSERT INTO backoffice_databaseauditlog (action, table_name, row_id, old_values, new_values, timestamp)
                VALUES (
                    'DELETE',
                    'licensing_license',
                    OLD.id,
                    'License Key: ' || OLD.license_key || ' | User ID: ' || OLD.user_id,
                    NULL,
                    datetime('now')
                );
            END;

            CREATE TRIGGER IF NOT EXISTS audit_order_insert
            AFTER INSERT ON payments_order
            BEGIN
                INSERT INTO backoffice_databaseauditlog (action, table_name, row_id, old_values, new_values, timestamp)
                VALUES (
                    'INSERT',
                    'payments_order',
                    NEW.id,
                    NULL,
                    'Total: ' || NEW.total_amount || ' | Status: ' || NEW.status || ' | User ID: ' || NEW.user_id || ' | Stripe ID: ' || COALESCE(NEW.stripe_payment_intent_id, 'NULL'),
                    datetime('now')
                );
            END;

            CREATE TRIGGER IF NOT EXISTS audit_order_update
            AFTER UPDATE ON payments_order
            BEGIN
                INSERT INTO backoffice_databaseauditlog (action, table_name, row_id, old_values, new_values, timestamp)
                VALUES (
                    'UPDATE',
                    'payments_order',
                    NEW.id,
                    'Status: ' || OLD.status || ' | Total: ' || OLD.total_amount,
                    'Status: ' || NEW.status || ' | Total: ' || NEW.total_amount,
                    datetime('now')
                );
            END;

            CREATE TRIGGER IF NOT EXISTS audit_order_delete
            AFTER DELETE ON payments_order
            BEGIN
                INSERT INTO backoffice_databaseauditlog (action, table_name, row_id, old_values, new_values, timestamp)
                VALUES (
                    'DELETE',
                    'payments_order',
                    OLD.id,
                    'User ID: ' || OLD.user_id || ' | Total: ' || OLD.total_amount,
                    NULL,
                    datetime('now')
                );
            END;
            """)
        elif vendor == 'mysql':
            cursor.execute("DROP TRIGGER IF EXISTS audit_license_insert;")
            cursor.execute("""
            CREATE TRIGGER audit_license_insert
            AFTER INSERT ON licensing_license
            FOR EACH ROW
            BEGIN
                INSERT INTO backoffice_databaseauditlog (action, table_name, row_id, old_values, new_values, timestamp)
                VALUES (
                    'INSERT',
                    'licensing_license',
                    NEW.id,
                    NULL,
                    CONCAT('License Key: ', NEW.license_key, ' | User ID: ', NEW.user_id, ' | Module ID: ', NEW.module_id, ' | Active: ', NEW.is_active),
                    NOW()
                );
            END;
            """)

            cursor.execute("DROP TRIGGER IF EXISTS audit_license_update;")
            cursor.execute("""
            CREATE TRIGGER audit_license_update
            AFTER UPDATE ON licensing_license
            FOR EACH ROW
            BEGIN
                INSERT INTO backoffice_databaseauditlog (action, table_name, row_id, old_values, new_values, timestamp)
                VALUES (
                    'UPDATE',
                    'licensing_license',
                    NEW.id,
                    CONCAT('Active: ', OLD.is_active, ' | Activations: ', OLD.activation_count, ' | Installation ID: ', COALESCE(OLD.installation_id, 'NULL')),
                    CONCAT('Active: ', NEW.is_active, ' | Activations: ', NEW.activation_count, ' | Installation ID: ', COALESCE(NEW.installation_id, 'NULL')),
                    NOW()
                );
            END;
            """)

            cursor.execute("DROP TRIGGER IF EXISTS audit_license_delete;")
            cursor.execute("""
            CREATE TRIGGER audit_license_delete
            AFTER DELETE ON licensing_license
            FOR EACH ROW
            BEGIN
                INSERT INTO backoffice_databaseauditlog (action, table_name, row_id, old_values, new_values, timestamp)
                VALUES (
                    'DELETE',
                    'licensing_license',
                    OLD.id,
                    CONCAT('License Key: ', OLD.license_key, ' | User ID: ', OLD.user_id),
                    NULL,
                    NOW()
                );
            END;
            """)

            cursor.execute("DROP TRIGGER IF EXISTS audit_order_insert;")
            cursor.execute("""
            CREATE TRIGGER audit_order_insert
            AFTER INSERT ON payments_order
            FOR EACH ROW
            BEGIN
                INSERT INTO backoffice_databaseauditlog (action, table_name, row_id, old_values, new_values, timestamp)
                VALUES (
                    'INSERT',
                    'payments_order',
                    NEW.id,
                    NULL,
                    CONCAT('Total: ', NEW.total_amount, ' | Status: ', NEW.status, ' | User ID: ', NEW.user_id, ' | Stripe ID: ', COALESCE(NEW.stripe_payment_intent_id, 'NULL')),
                    NOW()
                );
            END;
            """)

            cursor.execute("DROP TRIGGER IF EXISTS audit_order_update;")
            cursor.execute("""
            CREATE TRIGGER audit_order_update
            AFTER UPDATE ON payments_order
            FOR EACH ROW
            BEGIN
                INSERT INTO backoffice_databaseauditlog (action, table_name, row_id, old_values, new_values, timestamp)
                VALUES (
                    'UPDATE',
                    'payments_order',
                    NEW.id,
                    CONCAT('Status: ', OLD.status, ' | Total: ', OLD.total_amount),
                    CONCAT('Status: ', NEW.status, ' | Total: ', NEW.total_amount),
                    NOW()
                );
            END;
            """)

            cursor.execute("DROP TRIGGER IF EXISTS audit_order_delete;")
            cursor.execute("""
            CREATE TRIGGER audit_order_delete
            AFTER DELETE ON payments_order
            FOR EACH ROW
            BEGIN
                INSERT INTO backoffice_databaseauditlog (action, table_name, row_id, old_values, new_values, timestamp)
                VALUES (
                    'DELETE',
                    'payments_order',
                    OLD.id,
                    CONCAT('User ID: ', OLD.user_id, ' | Total: ', OLD.total_amount),
                    NULL,
                    NOW()
                );
            END;
            """)


def drop_triggers(apps, schema_editor):
    triggers = [
        'audit_license_insert',
        'audit_license_update',
        'audit_license_delete',
        'audit_order_insert',
        'audit_order_update',
        'audit_order_delete',
    ]
    with schema_editor.connection.cursor() as cursor:
        for t in triggers:
            cursor.execute(f"DROP TRIGGER IF EXISTS {t};")


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('licensing', '0001_initial'),
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DatabaseAuditLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=50, verbose_name='Action')),
                ('table_name', models.CharField(max_length=100, verbose_name='Table impactée')),
                ('row_id', models.IntegerField(verbose_name='ID de la ligne')),
                ('old_values', models.TextField(blank=True, null=True, verbose_name='Anciennes valeurs')),
                ('new_values', models.TextField(blank=True, null=True, verbose_name='Nouvelles valeurs')),
                ('timestamp', models.DateTimeField(auto_now_add=True, verbose_name='Date & Heure')),
            ],
            options={
                'verbose_name': 'Audit Base de Données',
                'verbose_name_plural': 'Audits Base de Données',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.RunPython(create_triggers, drop_triggers),
    ]

