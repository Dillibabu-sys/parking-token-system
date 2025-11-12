from django.db import models
from django.utils import timezone

class TwoWheelerEntry(models.Model):
    token_id = models.CharField(max_length=10, unique=True)
    vehicle_no = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=15, blank=True, null=True)  # Add this field
    entry_time = models.DateTimeField(default=timezone.now)
    exit_time = models.DateTimeField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.token_id} - {self.vehicle_no}"

class FourWheelerEntry(models.Model):
    token_id = models.CharField(max_length=10, unique=True)
    vehicle_no = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=15, blank=True, null=True)  # Add this field
    entry_time = models.DateTimeField(default=timezone.now)
    exit_time = models.DateTimeField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.token_id} - {self.vehicle_no}"

