from django.shortcuts import render_to_response

def index(request):
    print 'here!'
    return render_to_response('dkey/index.html')
