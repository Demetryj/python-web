from django.shortcuts import render

app_name = ""

# Create your views here.
def main(request):
    return render(request, 'quotes_app/main.html', context={"msg": "Hello world!"})