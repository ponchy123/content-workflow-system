from django.db import models
from apps.core.models import BaseModel, ServiceProvider


class ZipZone(BaseModel):
    id = models.AutoField(primary_key=True)
    provider = models.ForeignKey(ServiceProvider, on_delete=models.CASCADE)
    origin_zip = models.CharField(max_length=10)
    dest_zip_start = models.CharField(max_length=10)
    dest_zip_end = models.CharField(max_length=10)
    zone_number = models.IntegerField()

    class Meta:
        db_table = "zip_zones"
        indexes = [
            models.Index(fields=["origin_zip"], name="zip_zones_origin"),
            models.Index(fields=["dest_zip_start", "dest_zip_end"], name="zip_zones_dest"),
        ]
        unique_together = [("provider", "origin_zip", "dest_zip_start", "dest_zip_end")]

    def __str__(self):
        return f"{self.origin_zip} -> {self.dest_zip_start}-{self.dest_zip_end}: Zone {self.zone_number}"


class RemoteArea(BaseModel):
    provider = models.ForeignKey(ServiceProvider, on_delete=models.CASCADE)
    origin_zip = models.CharField(max_length=10)
    zip_code = models.CharField(max_length=10)
    remote_level = models.CharField(max_length=50, default="1")

    class Meta:
        db_table = "remote_areas"
        indexes = [
            models.Index(fields=["origin_zip"], name="remote_origin"),
            models.Index(fields=["zip_code"], name="remote_dest"),
        ]
        unique_together = [("provider", "origin_zip", "zip_code")]

    def __str__(self):
        return f"{self.zip_code} (Level {self.remote_level})" 