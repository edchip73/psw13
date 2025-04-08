from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from .models import Mentorados, Navigators, DisponibilidadeHorarios, Reuniao, Tarefa, Upload
from django.contrib import messages
from django.contrib.messages import constants
from datetime import timedelta
from datetime import datetime
from .auth import valida_token
from django.shortcuts import render
from babel.dates import format_date
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

@login_required

# Create your views here.
def mentorados(request):
    if request.method == 'GET':
        navigators = Navigators.objects.filter(user=request.user)
        mentorados = Mentorados.objects.filter(user=request.user)

        estagios_flat = [i[1] for i in Mentorados.estagio_choices]
        qtd_estagios = []
        for i, j in Mentorados.estagio_choices:
            x = Mentorados.objects.filter(estagio=i).filter(user=request.user).count()
            qtd_estagios.append(x)

        return render(request, 'mentorados.html', {'estagios': Mentorados.estagio_choices, 'navigators': 
        navigators, 'mentorados': mentorados, 'estagios_flat': estagios_flat, 'qtd_estagios': qtd_estagios})
    elif request.method == 'POST':
        nome = request.POST.get('nome')
        foto = request.FILES.get('foto')
        estagio = request.POST.get("estagio")
        navigator = request.POST.get('navigator')

        mentorado = Mentorados(
            nome=nome,
            foto=foto,
            estagio=estagio,
            navigator_id=navigator,
            user=request.user
        )
        mentorado.save()

        messages.add_message(request, constants.SUCCESS, 'Mentorado cadastrado com sucesso.')
        return redirect('mentorados')
@login_required    
def reunioes(request):
    if request.method == 'GET':
        reunioes = Reuniao.objects.filter(data__mentor=request.user)
        return render(request, 'reunioes.html', {'reunioes':reunioes})
    else:
        data = request.POST.get('data')

        data = datetime.strptime(data, '%Y-%m-%dT%H:%M')

        disponibilidades = DisponibilidadeHorarios.objects.filter(
            data_inicial__gte=(data - timedelta(minutes=50)),
            data_inicial__lte=(data + timedelta(minutes=50))
        )

        if disponibilidades.exists():
            messages.add_message(request, constants.ERROR, 'Você já possui uma reunião em aberto.')
            return redirect('reunioes')

        disponibilidade = DisponibilidadeHorarios(
            data_inicial=data,
            mentor=request.user

        )
        disponibilidade.save()

        messages.add_message(request, constants.SUCCESS, 'Horário disponibilizado com sucesso.')
        return redirect('reunioes')
@login_required  
def auth(request):
    if request.method == 'GET':
        return render(request, 'auth_mentorado.html')   
    elif request.method == 'POST':
        token = request.POST.get('token')

        if not Mentorados.objects.filter(token=token).exists():
            messages.add_message(request, constants.ERROR, 'Token inválido.')
            return redirect('auth_mentorado')
        
        response = redirect('escolher_dia')
        response.set_cookie('auth_token', token, max_age=3600)

        return response
@login_required    
def escolher_dia(request):
    if not valida_token(request.COOKIES.get('auth_token')):
        return redirect('auth_mentorado')
    
    if request.method == 'GET':
        mentorado = valida_token(request.COOKIES.get('auth_token'))
        disponibilidades = DisponibilidadeHorarios.objects.filter(
            data_inicial__gte=datetime.now(),
            agendado=False,
            mentor=mentorado.user
        ).values_list('data_inicial', flat=True)
        datas = []
        for i in disponibilidades:
            data_formatada = i.date().strftime('%d-%m-%Y')
            dia_semana = format_date(i.date(), "EEEE", locale='pt_BR').capitalize()
            datas.append((data_formatada, dia_semana))


        return render(request, 'escolher_dia.html', {'horarios': list(set(datas))})
@login_required
def agendar_reuniao(request):
    mentorado = valida_token(request.COOKIES.get('auth_token'))
    if not valida_token(request.COOKIES.get('auth_token')):
        return redirect('auth_mentorado')
    
    if request.method == 'GET':
        data = request.GET.get("data")

        
        
        if not data:
            # Data não foi enviada – renderiza só o formulário vazio
            return render(request, 'agendar_reuniao.html', {
                'horarios': None,
                'tags': Reuniao.tag_choices,
                'erro': 'Selecione uma data para agendar a reunião.'
            })

        try:
            data = datetime.strptime(data, '%d-%m-%Y')
        except ValueError:
            return render(request, 'agendar_reuniao.html', {
                'horarios': None,
                'tags': Reuniao.tag_choices,
                'erro': 'Formato de data inválido. Use DD-MM-AAAA.'
            })

        horarios = DisponibilidadeHorarios.objects.filter(
            data_inicial__gte=data,
            data_inicial__lt=data + timedelta(days=1),
            agendado=False,
            mentor=mentorado.user
        )

        print(f"Data buscada: {data}")
        print(f"Horários encontrados: {horarios.count()}")
        for h in horarios:
            print(h.data_inicial)


        return render(request, 'agendar_reuniao.html', {
            'horarios': horarios,
            'tags': Reuniao.tag_choices
        })
    else:
        horario_id = request.POST.get('horario')
        tag = request.POST.get('tag')
        descricao = request.POST.get('descricao')

        reuniao = Reuniao(
            data_id=horario_id,
            mentorado=mentorado,
            tag=tag,
            descricao=descricao
        )
        reuniao.save()

        horario = DisponibilidadeHorarios.objects.get(id=horario_id)
        horario.agendado = True
        horario.save()

        messages.add_message(request, constants.SUCCESS, 'Reunião agendada com sucesso.')
        return redirect('escolher_dia')
@login_required    
def tarefa(request, id):
    mentorado = Mentorados.objects.get(id=id)
    if mentorado.user != request.user:
        raise Http404()
    
    if request.method == 'GET':
        tarefas = Tarefa.objects.filter(mentorado=mentorado)
        videos = Upload.objects.filter(mentorado=mentorado)
        return render(request, 'tarefa.html', {'mentorado':mentorado, 'tarefas':tarefas, 'videos': videos})
    else:
        tarefa = request.POST.get('tarefa')

    t = Tarefa(
        mentorado=mentorado,
        tarefa=tarefa,
    )
    t.save()

    return redirect(f'/mentorados/tarefa/{id}')
@login_required
def upload(request, id):
    mentorado = Mentorados.objects.get(id=id)
    if mentorado.user != request.user:
        raise Http404()
    
    video = request.FILES.get('video')
    upload = Upload(
        mentorado=mentorado,
        video=video
    )
    upload.save()
    return redirect(f'/mentorados/tarefa/{id}')
@login_required
def tarefa_mentorado(request):
    mentorado = valida_token(request.COOKIES.get('auth_token'))
    if not mentorado:
        return redirect('auth_mentorado')
    
    if request.method == 'GET':
        videos = Upload.objects.filter(mentorado=mentorado)
        tarefas = Tarefa.objects.filter(mentorado=mentorado)
        return render(request, 'tarefa_mentorado.html', {'mentorado': mentorado, 'videos': videos, 'tarefas': tarefas})
@login_required    
@csrf_exempt
def tarefa_alterar(request, id):
    mentorado = valida_token(request.COOKIES.get('auth_token'))
    if not mentorado:
        return redirect('auth_mentorado')

    tarefa = Tarefa.objects.get(id=id)
    if mentorado != tarefa.mentorado:
        raise Http404()
    tarefa.realizada = not tarefa.realizada
    tarefa.save()

    return HttpResponse('teste')
