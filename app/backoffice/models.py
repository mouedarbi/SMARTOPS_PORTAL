from django.db import models

class DatabaseAuditLog(models.Model):
    """
    Modèle d'audit au niveau de la base de données SQLite.
    Alimenté directement par des TRIGGERS SQL pour tracer les modifications
    de données (DDL / DML) y compris hors de l'interface Django.
    """
    action = models.CharField(max_length=50, verbose_name="Action") # INSERT, UPDATE, DELETE
    table_name = models.CharField(max_length=100, verbose_name="Table impactée")
    row_id = models.IntegerField(verbose_name="ID de la ligne")
    old_values = models.TextField(null=True, blank=True, verbose_name="Anciennes valeurs")
    new_values = models.TextField(null=True, blank=True, verbose_name="Nouvelles valeurs")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Date & Heure")

    class Meta:
        verbose_name = "Audit Base de Données"
        verbose_name_plural = "Audits Base de Données"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action} sur {self.table_name} (ID: {self.row_id}) à {self.timestamp}"
