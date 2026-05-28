import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from organizations.models import Organization
from ingestion.models import DataSource

org, _ = Organization.objects.get_or_create(name="Acme Corp", industry="Tech")

ds_utility, _ = DataSource.objects.get_or_create(organization=org, source_type="UTILITY", ingestion_method="manual")
ds_sap, _ = DataSource.objects.get_or_create(organization=org, source_type="SAP", ingestion_method="manual")
ds_travel, _ = DataSource.objects.get_or_create(organization=org, source_type="TRAVEL", ingestion_method="manual")

print("Created DataSources:")
print(f"UTILITY - ID: {ds_utility.id}")
print(f"SAP - ID: {ds_sap.id}")
print(f"TRAVEL - ID: {ds_travel.id}")
