from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages

def  login_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(
            request,
            username=username,
            password=password
        )

        print("USERNAME:", username)
        print("USER:", user)

        if user is not None:
            login(request, user)
            print("LOGIN SUCCESSFUL")
            return redirect('home')
        else:
            print("LOGIN FAILED")
            return redirect('login')

    return render(request, 'authenticate/login.html')

@login_required
def home(request):
    return render('sawanih:dashboard')