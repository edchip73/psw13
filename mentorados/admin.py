from django.contrib import admin
from .models import Navigators, Mentorados, DisponibilidadeHorarios, Reuniao, Tarefa, Upload

# Register your models here.
admin.site.register(Navigators)
admin.site.register(Mentorados)
admin.site.register(DisponibilidadeHorarios)
admin.site.register(Reuniao)
admin.site.register(Tarefa)
admin.site.register(Upload)