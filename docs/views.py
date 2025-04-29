from django.shortcuts import render


def uap(request):
    return render(request, 'docs/about_us/uap.html')
