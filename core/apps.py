from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # Import models here to avoid circular imports
        from django.db.models.signals import post_save
        from laboratory.models import LabTestRequest, TestResult
        from pharmacy.models import Prescription
        from .models import create_lab_notification, create_lab_result_notification, create_prescription_notification
        
        # Connect signals
        post_save.connect(create_lab_notification, sender=LabTestRequest)
        post_save.connect(create_lab_result_notification, sender=TestResult)
        post_save.connect(create_prescription_notification, sender=Prescription)