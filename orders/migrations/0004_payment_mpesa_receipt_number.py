from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0003_alter_order_cart"),
    ]

    operations = [
        migrations.AddField(
            model_name="payment",
            name="mpesa_receipt_number",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]