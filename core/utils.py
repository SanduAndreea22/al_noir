from django.http import JsonResponse


def is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def form_json_response(form, success_message):
    if form.is_valid():
        form.save()
        return JsonResponse({'success': True, 'message': success_message})
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)


_RO_DIACRITICS = str.maketrans({
    'ă': 'a', 'Ă': 'A',
    'ș': 's', 'Ș': 'S', 'ş': 's', 'Ş': 'S',
    'ț': 't', 'Ț': 'T', 'ţ': 't', 'Ţ': 'T',
})


def transliterate_ro(value):
    """Strip Romanian diacritics that fall outside WinAnsi/Latin-1 (ă, ș/ş, ț/ţ)."""
    return value.translate(_RO_DIACRITICS)
